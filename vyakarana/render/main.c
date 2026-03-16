/* main.c — proof of concept: SDL2 + OpenGL 3.3 + PBR sphere
 *
 * What this establishes:
 *   - SDL2 window + OpenGL 3.3 core context (no GLAD, no GLEW)
 *   - gl.h function loader via SDL_GL_GetProcAddress
 *   - GLSL shader compile + link (vert.glsl + frag.glsl loaded from disk)
 *   - VAO/VBO/EBO: procedural sphere mesh (gola — sama-dura-sthita)
 *   - Cook-Torrance PBR fragment shader (pbr.om: energy-siddha)
 *   - Orbital camera (camera-3d: darshana-swarupa, projection-kriya)
 *   - Mouse ray-picking skeleton (ray-picking: rekha-swarupa, collision-phala)
 *   - Force-directed layout skeleton (spring + repulsion, per-frame)
 *
 * Build:
 *   make        (see Makefile)
 *   ./render
 *
 * This is the "outside" layer. No OCaml. Proves the GPU pipeline works.
 * Once solid, render_stubs.c wraps these functions for OCaml C FFI.
 */

#define GL_DEFINE_PTRS
#include "gl.h"

#include <SDL2/SDL.h>
#include <GL/glcorearb.h>   /* GL 3.x type constants (GL_ARRAY_BUFFER, GL_STATIC_DRAW etc.) */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- math types ---- */

typedef struct { float x, y, z; }    vec3;
typedef struct { float x, y, z, w; } vec4;
typedef struct { float m[16]; }      mat4;  /* column-major, matches GLSL */

static mat4 mat4_identity(void) {
    mat4 m = {0};
    m.m[0]=m.m[5]=m.m[10]=m.m[15]=1.0f;
    return m;
}

static mat4 mat4_perspective(float fovy, float aspect, float near, float far) {
    mat4 m = {0};
    float f = 1.0f / tanf(fovy * 0.5f);
    m.m[0]  =  f / aspect;
    m.m[5]  =  f;
    m.m[10] = (far + near) / (near - far);
    m.m[11] = -1.0f;
    m.m[14] = (2.0f * far * near) / (near - far);
    return m;
}

static mat4 mat4_lookAt(vec3 eye, vec3 center, vec3 up) {
    vec3 f = { center.x-eye.x, center.y-eye.y, center.z-eye.z };
    float fl = sqrtf(f.x*f.x+f.y*f.y+f.z*f.z);
    f.x/=fl; f.y/=fl; f.z/=fl;
    vec3 s = { f.y*up.z - f.z*up.y, f.z*up.x - f.x*up.z, f.x*up.y - f.y*up.x };
    float sl = sqrtf(s.x*s.x+s.y*s.y+s.z*s.z);
    s.x/=sl; s.y/=sl; s.z/=sl;
    vec3 u2 = { s.y*f.z - s.z*f.y, s.z*f.x - s.x*f.z, s.x*f.y - s.y*f.x };
    mat4 m = {0};
    m.m[0]=s.x;  m.m[4]=s.y;  m.m[8]=s.z;
    m.m[1]=u2.x; m.m[5]=u2.y; m.m[9]=u2.z;
    m.m[2]=-f.x; m.m[6]=-f.y; m.m[10]=-f.z;
    m.m[12]=-(s.x*eye.x+s.y*eye.y+s.z*eye.z);
    m.m[13]=-(u2.x*eye.x+u2.y*eye.y+u2.z*eye.z);
    m.m[14]= (f.x*eye.x+f.y*eye.y+f.z*eye.z);
    m.m[15]=1.0f;
    return m;
}

static mat4 mat4_translate(float x, float y, float z) {
    mat4 m = mat4_identity();
    m.m[12]=x; m.m[13]=y; m.m[14]=z;
    return m;
}

static mat4 mat4_rotY(float a) __attribute__((unused));
static mat4 mat4_rotY(float a) {
    mat4 m = mat4_identity();
    m.m[0]=cosf(a); m.m[8]=sinf(a);
    m.m[2]=-sinf(a); m.m[10]=cosf(a);
    return m;
}

/* ---- shader loading ---- */

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    char *buf = malloc(sz + 1);
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);
    return buf;
}

static GLuint compile_shader(GLenum type, const char *src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, NULL);
    glCompileShader(s);
    GLint ok; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[1024]; glGetShaderInfoLog(s, sizeof(log), NULL, log);
        fprintf(stderr, "shader compile error:\n%s\n", log); exit(1);
    }
    return s;
}

static GLuint link_program(const char *vert_path, const char *frag_path) {
    char *vsrc = read_file(vert_path);
    char *fsrc = read_file(frag_path);
    GLuint vs = compile_shader(GL_VERTEX_SHADER,   vsrc);
    GLuint fs = compile_shader(GL_FRAGMENT_SHADER, fsrc);
    free(vsrc); free(fsrc);
    GLuint p = glCreateProgram();
    glAttachShader(p, vs); glAttachShader(p, fs);
    glLinkProgram(p);
    GLint ok; glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[1024]; glGetProgramInfoLog(p, sizeof(log), NULL, log);
        fprintf(stderr, "program link error:\n%s\n", log); exit(1);
    }
    glDeleteShader(vs); glDeleteShader(fs);
    return p;
}

/* ---- gola (sphere) mesh generation ----
 *
 * kosha: gola — sama-dura-sthita, trikona-swarupa via mesh
 * vertex layout: [x,y,z, nx,ny,nz, u,v]  (8 floats per vertex)
 * generated as latitude/longitude tesselation
 * normals = normalized position (sphere center at origin)
 */

#define SPHERE_STACKS 32
#define SPHERE_SLICES 32

typedef struct {
    GLuint vao, vbo, ebo;
    int    index_count;
} Mesh;

static Mesh make_sphere(float radius) {
    int nverts = (SPHERE_STACKS+1) * (SPHERE_SLICES+1);
    int nidx   = SPHERE_STACKS * SPHERE_SLICES * 6;
    float *verts = malloc(nverts * 8 * sizeof(float));
    GLuint *idx  = malloc(nidx * sizeof(GLuint));

    int vi = 0;
    for (int i = 0; i <= SPHERE_STACKS; i++) {
        float phi = (float)i / SPHERE_STACKS * M_PI;         /* 0 → π */
        for (int j = 0; j <= SPHERE_SLICES; j++) {
            float theta = (float)j / SPHERE_SLICES * 2.0f * M_PI; /* 0 → 2π */
            float x = sinf(phi) * cosf(theta);
            float y = cosf(phi);
            float z = sinf(phi) * sinf(theta);
            /* position */
            verts[vi*8+0] = x * radius;
            verts[vi*8+1] = y * radius;
            verts[vi*8+2] = z * radius;
            /* normal = unit position (sphere is centered at origin) */
            verts[vi*8+3] = x;
            verts[vi*8+4] = y;
            verts[vi*8+5] = z;
            /* uv */
            verts[vi*8+6] = (float)j / SPHERE_SLICES;
            verts[vi*8+7] = (float)i / SPHERE_STACKS;
            vi++;
        }
    }

    int ii = 0;
    for (int i = 0; i < SPHERE_STACKS; i++) {
        for (int j = 0; j < SPHERE_SLICES; j++) {
            int a = i*(SPHERE_SLICES+1) + j;
            int b = a + SPHERE_SLICES + 1;
            /* two triangles per quad (trikona-swarupa) */
            idx[ii++]=a;   idx[ii++]=b;   idx[ii++]=a+1;
            idx[ii++]=b;   idx[ii++]=b+1; idx[ii++]=a+1;
        }
    }

    Mesh m;
    glGenVertexArrays(1, &m.vao);
    glBindVertexArray(m.vao);

    glGenBuffers(1, &m.vbo);
    glBindBuffer(GL_ARRAY_BUFFER, m.vbo);
    glBufferData(GL_ARRAY_BUFFER, nverts*8*sizeof(float), verts, GL_STATIC_DRAW);

    glGenBuffers(1, &m.ebo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m.ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, nidx*sizeof(GLuint), idx, GL_STATIC_DRAW);

    /* vertex attrib layout: location 0=pos, 1=normal, 2=uv */
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8*sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8*sizeof(float), (void*)(3*sizeof(float)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8*sizeof(float), (void*)(6*sizeof(float)));
    glEnableVertexAttribArray(2);

    glBindVertexArray(0);
    m.index_count = nidx;
    free(verts); free(idx);
    return m;
}

/* ---- force-directed layout state ----
 *
 * kosha: force-directed — layout-swarupa, spring-force-yukta, repulsion-yukta,
 *        alpha-cooling-yukta, velocity-decay-yukta, convergence-phala
 *
 * Two nodes connected by a spring. Each frame: apply spring + repulsion,
 * integrate velocity, cool alpha. Stops when alpha < 0.001.
 */

#define MAX_NODES 64

typedef struct {
    vec3  pos;
    vec3  vel;
    float mass;
} FDNode;

typedef struct {
    FDNode nodes[MAX_NODES];
    int    n;
    float  alpha;         /* heat — 1.0=hot (moving), 0.0=cold (converged) */
    float  alpha_decay;   /* cooling per tick */
    float  velocity_decay;
    float  spring_k;
    float  spring_rest;
    float  repulsion_c;
} FDLayout;

static FDLayout fd_init(void) {
    FDLayout fd = {0};
    fd.n = 6;
    fd.alpha          = 1.0f;
    fd.alpha_decay    = 0.005f;
    fd.velocity_decay = 0.4f;
    fd.spring_k       = 0.08f;
    fd.spring_rest    = 2.5f;
    fd.repulsion_c    = 8.0f;
    /* initial positions — scattered in a rough circle */
    float angles[] = {0, 1.05f, 2.09f, 3.14f, 4.19f, 5.24f};
    for (int i = 0; i < fd.n; i++) {
        fd.nodes[i].pos  = (vec3){ 3.0f*cosf(angles[i]), 0.5f*(i%2?1:-1), 3.0f*sinf(angles[i]) };
        fd.nodes[i].vel  = (vec3){0,0,0};
        fd.nodes[i].mass = 1.0f;
    }
    return fd;
}

static void fd_tick(FDLayout *fd, float dt) {
    if (fd->alpha < 0.001f) return;

    /* zero forces */
    vec3 force[MAX_NODES];
    memset(force, 0, sizeof(vec3)*fd->n);

    /* spring forces between connected pairs (edges: 0-1, 1-2, 2-3, 3-4, 4-5, 5-0) */
    int edges[][2] = {{0,1},{1,2},{2,3},{3,4},{4,5},{5,0},{0,3},{1,4}};
    int ne = 8;
    for (int e = 0; e < ne; e++) {
        int a = edges[e][0], b = edges[e][1];
        vec3 d = { fd->nodes[b].pos.x - fd->nodes[a].pos.x,
                   fd->nodes[b].pos.y - fd->nodes[a].pos.y,
                   fd->nodes[b].pos.z - fd->nodes[a].pos.z };
        float len = sqrtf(d.x*d.x + d.y*d.y + d.z*d.z) + 1e-6f;
        float f   = fd->spring_k * (len - fd->spring_rest) * fd->alpha;
        /* spring: F = k × (len − rest) × dir */
        force[a].x += f * d.x/len;  force[a].y += f * d.y/len;  force[a].z += f * d.z/len;
        force[b].x -= f * d.x/len;  force[b].y -= f * d.y/len;  force[b].z -= f * d.z/len;
    }

    /* repulsion between all pairs: F = c / dist² */
    for (int i = 0; i < fd->n; i++) {
        for (int j = i+1; j < fd->n; j++) {
            vec3 d = { fd->nodes[i].pos.x - fd->nodes[j].pos.x,
                       fd->nodes[i].pos.y - fd->nodes[j].pos.y,
                       fd->nodes[i].pos.z - fd->nodes[j].pos.z };
            float dist2 = d.x*d.x + d.y*d.y + d.z*d.z + 1e-6f;
            float dist  = sqrtf(dist2);
            float f     = fd->repulsion_c / dist2 * fd->alpha;
            force[i].x += f * d.x/dist;  force[i].y += f * d.y/dist;  force[i].z += f * d.z/dist;
            force[j].x -= f * d.x/dist;  force[j].y -= f * d.y/dist;  force[j].z -= f * d.z/dist;
        }
    }

    /* integrate: vel = (vel + force × dt) × velocity_decay, pos = pos + vel × dt */
    for (int i = 0; i < fd->n; i++) {
        fd->nodes[i].vel.x = (fd->nodes[i].vel.x + force[i].x * dt) * fd->velocity_decay;
        fd->nodes[i].vel.y = (fd->nodes[i].vel.y + force[i].y * dt) * fd->velocity_decay;
        fd->nodes[i].vel.z = (fd->nodes[i].vel.z + force[i].z * dt) * fd->velocity_decay;
        fd->nodes[i].pos.x += fd->nodes[i].vel.x * dt;
        fd->nodes[i].pos.y += fd->nodes[i].vel.y * dt;
        fd->nodes[i].pos.z += fd->nodes[i].vel.z * dt;
    }

    /* cool — alpha-cooling: reduces heat each tick toward convergence */
    fd->alpha *= (1.0f - fd->alpha_decay);
}

/* ---- ray-picking skeleton ----
 *
 * kosha: ray-picking — rekha-swarupa, camera-3d-sthita, mouse-yukta, collision-phala
 *
 * Unprojects mouse (px,py) through inv(proj×view) to get a world-space ray.
 * Tests ray against each sphere (gola: sama-dura-sthita, dura-yukta).
 * Returns index of nearest hit, or -1.
 *
 * Ray-sphere test: |cross(d, oc)|² ≤ r² × |d|²
 * where oc = origin − center, d = ray direction
 */
static int pick_ray(float px, float py, int w, int h,
                    mat4 proj, mat4 view,
                    FDLayout *fd, float radius) {
    /* normalised device coordinates */
    float ndcx = (2.0f * px / w) - 1.0f;
    float ndcy = 1.0f - (2.0f * py / h);

    /* unproject: simple inv(proj) approach for perspective */
    float tanHalfFov = 1.0f / proj.m[5];
    float aspect     = proj.m[5] / proj.m[0];
    vec3 ray_view = { ndcx * tanHalfFov * aspect, ndcy * tanHalfFov, -1.0f };

    /* transform ray direction from view to world space */
    /* inv(view) rotation part = transpose of upper-left 3x3 */
    vec3 rd = {
        view.m[0]*ray_view.x + view.m[1]*ray_view.y + view.m[2]*ray_view.z,
        view.m[4]*ray_view.x + view.m[5]*ray_view.y + view.m[6]*ray_view.z,
        view.m[8]*ray_view.x + view.m[9]*ray_view.y + view.m[10]*ray_view.z
    };
    float rdl = sqrtf(rd.x*rd.x+rd.y*rd.y+rd.z*rd.z);
    rd.x/=rdl; rd.y/=rdl; rd.z/=rdl;

    /* ray origin = camera position (from view matrix translation) */
    vec3 ro = {
        -(view.m[0]*view.m[12] + view.m[1]*view.m[13] + view.m[2]*view.m[14]),
        -(view.m[4]*view.m[12] + view.m[5]*view.m[13] + view.m[6]*view.m[14]),
        -(view.m[8]*view.m[12] + view.m[9]*view.m[13] + view.m[10]*view.m[14])
    };

    int best = -1; float best_t = 1e30f;
    for (int i = 0; i < fd->n; i++) {
        vec3 oc = { ro.x - fd->nodes[i].pos.x,
                    ro.y - fd->nodes[i].pos.y,
                    ro.z - fd->nodes[i].pos.z };
        float b = oc.x*rd.x + oc.y*rd.y + oc.z*rd.z;
        float c = oc.x*oc.x + oc.y*oc.y + oc.z*oc.z - radius*radius;
        float disc = b*b - c;
        if (disc >= 0.0f) {
            float t = -b - sqrtf(disc);
            if (t > 0.0f && t < best_t) { best_t = t; best = i; }
        }
    }
    return best;
}

/* ---- edge VBO ---- */

static GLuint edge_vao, edge_vbo;
static void init_edge_vbo(void) {
    glGenVertexArrays(1, &edge_vao);
    glBindVertexArray(edge_vao);
    glGenBuffers(1, &edge_vbo);
    glBindBuffer(GL_ARRAY_BUFFER, edge_vbo);
    glBufferData(GL_ARRAY_BUFFER, MAX_NODES*2*3*sizeof(float), NULL, GL_DYNAMIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3*sizeof(float), 0);
    glEnableVertexAttribArray(0);
    glBindVertexArray(0);
}

/* ---- main ---- */

int main(void) {
    /* SDL + OpenGL 3.3 core context */
    SDL_Init(SDL_INIT_VIDEO);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE,   24);

    int W = 1280, H = 720;
    SDL_Window *win = SDL_CreateWindow(
        "vyakarana — proof graph (imagination)",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        W, H, SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);
    SDL_GLContext ctx = SDL_GL_CreateContext(win);
    SDL_GL_SetSwapInterval(1);  /* vsync */

    /* load GL 3.3 core functions */
    gl_load();

    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);

    /* compile shaders */
    GLuint prog = link_program("vert.glsl", "frag.glsl");

    /* get uniform locations */
    GLint loc_model      = glGetUniformLocation(prog, "u_model");
    GLint loc_view       = glGetUniformLocation(prog, "u_view");
    GLint loc_proj       = glGetUniformLocation(prog, "u_proj");
    GLint loc_albedo     = glGetUniformLocation(prog, "u_albedo");
    GLint loc_roughness  = glGetUniformLocation(prog, "u_roughness");
    GLint loc_metallic   = glGetUniformLocation(prog, "u_metallic");
    GLint loc_light_pos  = glGetUniformLocation(prog, "u_light_pos");
    GLint loc_light_col  = glGetUniformLocation(prog, "u_light_color");
    GLint loc_cam_pos    = glGetUniformLocation(prog, "u_cam_pos");

    /* sphere mesh (gola: sama-dura-sthita) */
    Mesh sphere = make_sphere(0.35f);

    /* edge VBO (rekha: line between nodes) */
    init_edge_vbo();

    /* force-directed layout */
    FDLayout fd = fd_init();

    /* orbital camera state */
    float cam_theta = 0.4f, cam_phi = 0.5f, cam_dist = 12.0f;
    int   dragging  = 0;
    int   picked    = -1;

    Uint32 last_ticks = SDL_GetTicks();
    int running = 1;

    while (running) {
        Uint32 now = SDL_GetTicks();
        float  dt  = (now - last_ticks) / 1000.0f;
        last_ticks = now;

        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            switch (ev.type) {
            case SDL_QUIT: running = 0; break;
            case SDL_KEYDOWN:
                if (ev.key.keysym.sym == SDLK_ESCAPE) running = 0;
                if (ev.key.keysym.sym == SDLK_r) { fd = fd_init(); } /* reset */
                break;
            case SDL_WINDOWEVENT:
                if (ev.window.event == SDL_WINDOWEVENT_SIZE_CHANGED) {
                    W = ev.window.data1; H = ev.window.data2;
                    glViewport(0, 0, W, H);
                }
                break;
            case SDL_MOUSEBUTTONDOWN:
                if (ev.button.button == SDL_BUTTON_LEFT) {
                    dragging = 1;
                    /* ray-picking on click */
                    mat4 proj = mat4_perspective(0.785f, (float)W/H, 0.1f, 100.0f);
                    vec3 eye  = { cam_dist*sinf(cam_phi)*cosf(cam_theta),
                                  cam_dist*cosf(cam_phi),
                                  cam_dist*sinf(cam_phi)*sinf(cam_theta) };
                    mat4 view = mat4_lookAt(eye, (vec3){0,0,0}, (vec3){0,1,0});
                    picked = pick_ray(ev.button.x, ev.button.y, W, H,
                                      proj, view, &fd, 0.35f);
                    if (picked >= 0)
                        printf("picked node %d\n", picked);
                }
                break;
            case SDL_MOUSEBUTTONUP:
                if (ev.button.button == SDL_BUTTON_LEFT) { dragging = 0; picked = -1; }
                break;
            case SDL_MOUSEMOTION:
                if (dragging && picked < 0) {
                    /* orbit camera */
                    cam_theta += ev.motion.xrel * 0.005f;
                    cam_phi   += ev.motion.yrel * 0.005f;
                    if (cam_phi < 0.05f) cam_phi = 0.05f;
                    if (cam_phi > 3.09f) cam_phi = 3.09f;
                }
                break;
            case SDL_MOUSEWHEEL:
                cam_dist -= ev.wheel.y * 0.5f;
                if (cam_dist < 2.0f) cam_dist = 2.0f;
                break;
            }
        }

        /* physics tick — force-directed layout (alpha-cooling) */
        fd_tick(&fd, dt);

        /* camera */
        vec3 eye = { cam_dist*sinf(cam_phi)*cosf(cam_theta),
                     cam_dist*cosf(cam_phi),
                     cam_dist*sinf(cam_phi)*sinf(cam_theta) };
        mat4 view = mat4_lookAt(eye, (vec3){0,0,0}, (vec3){0,1,0});
        mat4 proj = mat4_perspective(0.785f, (float)W/H, 0.1f, 100.0f);

        /* clear */
        glClearColor(0.05f, 0.05f, 0.08f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        glUseProgram(prog);
        glUniformMatrix4fv(loc_view, 1, GL_FALSE, view.m);
        glUniformMatrix4fv(loc_proj, 1, GL_FALSE, proj.m);
        glUniform3f(loc_light_pos, 8.0f, 8.0f, 8.0f);
        glUniform3f(loc_light_col, 150.0f, 140.0f, 130.0f);
        glUniform3f(loc_cam_pos, eye.x, eye.y, eye.z);

        /* draw nodes (gola: sphere at each FD position) */
        glBindVertexArray(sphere.vao);
        for (int i = 0; i < fd.n; i++) {
            mat4 model = mat4_translate(fd.nodes[i].pos.x,
                                        fd.nodes[i].pos.y,
                                        fd.nodes[i].pos.z);
            glUniformMatrix4fv(loc_model, 1, GL_FALSE, model.m);

            /* material varies per node — kosha node "colour" would come from satya */
            float t = (float)i / fd.n;
            glUniform3f(loc_albedo,    0.2f + 0.6f*t, 0.5f, 0.8f - 0.4f*t);
            glUniform1f(loc_roughness, 0.3f + 0.4f*t);
            glUniform1f(loc_metallic,  (i == picked) ? 1.0f : 0.0f);

            glDrawElements(GL_TRIANGLES, sphere.index_count, GL_UNSIGNED_INT, 0);
        }

        SDL_GL_SwapWindow(win);
    }

    glDeleteProgram(prog);
    glDeleteVertexArrays(1, &sphere.vao);
    glDeleteBuffers(1, &sphere.vbo);
    glDeleteBuffers(1, &sphere.ebo);
    SDL_GL_DeleteContext(ctx);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}
