#version 330 core

/* vertex shader — camera-3d: darshana-swarupa, projection-kriya
 *
 * Takes a vertex (bindu: position + normal + uv) in world-space.
 * Transforms it through model → view → projection to clip-space.
 * Passes normal and world-position to the fragment stage for PBR.
 *
 * Kosha:
 *   vertex     — bindu-swarupa, float-yukta, position-yukta normal-yukta
 *   camera-3d  — darshana-swarupa, projection-kriya, viewport-phala
 *   shader     — vertex-ahara, fragment-phala, gpu-kriya
 */

/* vertex attributes — the VBO layout (3 floats pos, 3 floats normal, 2 floats uv) */
layout (location = 0) in vec3 a_pos;
layout (location = 1) in vec3 a_normal;
layout (location = 2) in vec2 a_uv;

/* camera-3d: model × view × projection — collapses world-space to clip-space */
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;

/* pass to fragment stage */
out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world = u_model * vec4(a_pos, 1.0);
    v_world_pos = world.xyz;

    /* normal transform: use inverse-transpose of model for non-uniform scale */
    v_normal    = normalize(mat3(transpose(inverse(u_model))) * a_normal);
    v_uv        = a_uv;

    gl_Position = u_proj * u_view * world;
}
