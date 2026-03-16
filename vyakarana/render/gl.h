/* gl.h — minimal OpenGL 3.3 core function loader
 *
 * OpenGL functions split into two groups:
 *
 *   GL 1.x — directly exported from libGL.so. Declared extern here.
 *             Linked normally: -lGL. No proc address loading needed.
 *             glEnable, glDisable, glViewport, glClear, glClearColor,
 *             glDepthFunc, glDrawArrays, glDrawElements, glLineWidth, etc.
 *
 *   GL 2.0+ — only reachable via SDL_GL_GetProcAddress after context creation.
 *             VAO, VBO, shaders, uniforms, etc.
 *             Declared as function pointers, loaded by gl_load().
 *
 * Usage:
 *   1. Call SDL_GL_CreateContext first.
 *   2. Call gl_load() once.
 *   3. Use any function below normally.
 *
 * Kosha anchors:
 *   vertex      — bindu-swarupa, float-yukta     → VBO layout
 *   mesh        — trikona-swarupa, vertex-yukta   → VAO + EBO
 *   shader      — vertex-ahara, fragment-phala    → glCreateShader etc.
 *   rasterization — trikona-ahara, fragment-phala → glDrawElements (GL 1.1)
 */

#pragma once
#include <SDL2/SDL.h>
#include <GL/glcorearb.h>   /* PFNGL... typedefs for GL 2.0+ */
#include <stdio.h>
#include <stdlib.h>

/* ---- GL 1.x — direct exports from libGL.so (no proc loading needed) ----
 * Declare extern so we can call them without including GL/gl.h
 * (which conflicts with glcorearb.h on some definitions).
 */
typedef unsigned int  GLenum;
typedef unsigned int  GLbitfield;
typedef float         GLfloat;
typedef int           GLint;
typedef unsigned int  GLuint;
typedef int           GLsizei;
typedef unsigned char GLboolean;

/* These are regular C function declarations — linked via -lGL */
extern void  glEnable(GLenum cap);
extern void  glDisable(GLenum cap);
extern void  glDepthFunc(GLenum func);
extern void  glViewport(GLint x, GLint y, GLsizei w, GLsizei h);
extern void  glClearColor(GLfloat r, GLfloat g, GLfloat b, GLfloat a);
extern void  glClear(GLbitfield mask);
extern void  glDrawArrays(GLenum mode, GLint first, GLsizei count);
extern void  glDrawElements(GLenum mode, GLsizei count, GLenum type, const void *indices);
extern void  glLineWidth(GLfloat width);
extern void  glPointSize(GLfloat size);
extern void  glScissor(GLint x, GLint y, GLsizei w, GLsizei h);
extern void  glBlendFunc(GLenum sfactor, GLenum dfactor);
extern const GLubyte *glGetString(GLenum name);
extern void  glGetIntegerv(GLenum pname, GLint *data);

/* GL 1.x constants we use (not all in glcorearb.h) */
#ifndef GL_DEPTH_TEST
#define GL_DEPTH_TEST         0x0B71
#define GL_LESS               0x0201
#define GL_COLOR_BUFFER_BIT   0x00004000
#define GL_DEPTH_BUFFER_BIT   0x00000100
#define GL_TRIANGLES          0x0004
#define GL_LINES              0x0001
#define GL_LINE_STRIP         0x0003
#define GL_UNSIGNED_INT       0x1405
#define GL_FLOAT              0x1406
#define GL_FALSE              0
#define GL_TRUE               1
#define GL_BLEND              0x0BE2
#define GL_SRC_ALPHA          0x0302
#define GL_ONE_MINUS_SRC_ALPHA 0x0303
#endif

/* ---- GL 2.0+ function pointers (loaded via SDL_GL_GetProcAddress) ---- */

/* VAO (GL 3.0) */
extern PFNGLGENVERTEXARRAYSPROC         glGenVertexArrays;
extern PFNGLBINDVERTEXARRAYPROC         glBindVertexArray;
extern PFNGLDELETEVERTEXARRAYSPROC      glDeleteVertexArrays;

/* VBO / EBO (GL 1.5) */
extern PFNGLGENBUFFERSPROC              glGenBuffers;
extern PFNGLBINDBUFFERPROC              glBindBuffer;
extern PFNGLBUFFERDATAPROC              glBufferData;
extern PFNGLBUFFERSUBDATAPROC           glBufferSubData;
extern PFNGLDELETEBUFFERSPROC           glDeleteBuffers;

/* vertex attribs (GL 2.0) */
extern PFNGLVERTEXATTRIBPOINTERPROC     glVertexAttribPointer;
extern PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;

/* shaders — vertex-ahara, fragment-phala, gpu-kriya (GL 2.0) */
extern PFNGLCREATESHADERPROC            glCreateShader;
extern PFNGLSHADERSOURCEPROC            glShaderSource;
extern PFNGLCOMPILESHADERPROC           glCompileShader;
extern PFNGLGETSHADERIVPROC             glGetShaderiv;
extern PFNGLGETSHADERINFOLOGPROC        glGetShaderInfoLog;
extern PFNGLDELETESHADERPROC            glDeleteShader;

/* program (GL 2.0) */
extern PFNGLCREATEPROGRAMPROC           glCreateProgram;
extern PFNGLATTACHSHADERPROC            glAttachShader;
extern PFNGLLINKPROGRAMPROC             glLinkProgram;
extern PFNGLGETPROGRAMIVPROC            glGetProgramiv;
extern PFNGLGETPROGRAMINFOLOGPROC       glGetProgramInfoLog;
extern PFNGLUSEPROGRAMPROC              glUseProgram;
extern PFNGLDELETEPROGRAMPROC           glDeleteProgram;

/* uniforms — material: albedo, roughness, metallic; camera matrices (GL 2.0) */
extern PFNGLGETUNIFORMLOCATIONPROC      glGetUniformLocation;
extern PFNGLUNIFORM1FPROC               glUniform1f;
extern PFNGLUNIFORM1IPROC               glUniform1i;
extern PFNGLUNIFORM3FPROC               glUniform3f;
extern PFNGLUNIFORM3FVPROC              glUniform3fv;
extern PFNGLUNIFORM4FVPROC              glUniform4fv;
extern PFNGLUNIFORMMATRIX4FVPROC        glUniformMatrix4fv;

/* ---- macro to load one GL 2.0+ function pointer ---- */
#define GL_LOAD(type, name) \
    name = (type) SDL_GL_GetProcAddress(#name); \
    if (!name) { fprintf(stderr, "gl_load: failed to load " #name "\n"); exit(1); }

static inline void gl_load(void) {
    GL_LOAD(PFNGLGENVERTEXARRAYSPROC,          glGenVertexArrays)
    GL_LOAD(PFNGLBINDVERTEXARRAYPROC,          glBindVertexArray)
    GL_LOAD(PFNGLDELETEVERTEXARRAYSPROC,       glDeleteVertexArrays)
    GL_LOAD(PFNGLGENBUFFERSPROC,               glGenBuffers)
    GL_LOAD(PFNGLBINDBUFFERPROC,               glBindBuffer)
    GL_LOAD(PFNGLBUFFERDATAPROC,               glBufferData)
    GL_LOAD(PFNGLBUFFERSUBDATAPROC,            glBufferSubData)
    GL_LOAD(PFNGLDELETEBUFFERSPROC,            glDeleteBuffers)
    GL_LOAD(PFNGLVERTEXATTRIBPOINTERPROC,      glVertexAttribPointer)
    GL_LOAD(PFNGLENABLEVERTEXATTRIBARRAYPROC,  glEnableVertexAttribArray)
    GL_LOAD(PFNGLCREATESHADERPROC,             glCreateShader)
    GL_LOAD(PFNGLSHADERSOURCEPROC,             glShaderSource)
    GL_LOAD(PFNGLCOMPILESHADERPROC,            glCompileShader)
    GL_LOAD(PFNGLGETSHADERIVPROC,              glGetShaderiv)
    GL_LOAD(PFNGLGETSHADERINFOLOGPROC,         glGetShaderInfoLog)
    GL_LOAD(PFNGLDELETESHADERPROC,             glDeleteShader)
    GL_LOAD(PFNGLCREATEPROGRAMPROC,            glCreateProgram)
    GL_LOAD(PFNGLATTACHSHADERPROC,             glAttachShader)
    GL_LOAD(PFNGLLINKPROGRAMPROC,              glLinkProgram)
    GL_LOAD(PFNGLGETPROGRAMIVPROC,             glGetProgramiv)
    GL_LOAD(PFNGLGETPROGRAMINFOLOGPROC,        glGetProgramInfoLog)
    GL_LOAD(PFNGLUSEPROGRAMPROC,               glUseProgram)
    GL_LOAD(PFNGLDELETEPROGRAMPROC,            glDeleteProgram)
    GL_LOAD(PFNGLGETUNIFORMLOCATIONPROC,       glGetUniformLocation)
    GL_LOAD(PFNGLUNIFORM1FPROC,                glUniform1f)
    GL_LOAD(PFNGLUNIFORM1IPROC,                glUniform1i)
    GL_LOAD(PFNGLUNIFORM3FPROC,                glUniform3f)
    GL_LOAD(PFNGLUNIFORM3FVPROC,               glUniform3fv)
    GL_LOAD(PFNGLUNIFORM4FVPROC,               glUniform4fv)
    GL_LOAD(PFNGLUNIFORMMATRIX4FVPROC,         glUniformMatrix4fv)
}

/* ---- definitions block — include in exactly one .c file ----
 *
 * In your .c file:   #define GL_DEFINE_PTRS
 *                    #include "gl.h"
 */
#ifdef GL_DEFINE_PTRS
PFNGLGENVERTEXARRAYSPROC         glGenVertexArrays;
PFNGLBINDVERTEXARRAYPROC         glBindVertexArray;
PFNGLDELETEVERTEXARRAYSPROC      glDeleteVertexArrays;
PFNGLGENBUFFERSPROC              glGenBuffers;
PFNGLBINDBUFFERPROC              glBindBuffer;
PFNGLBUFFERDATAPROC              glBufferData;
PFNGLBUFFERSUBDATAPROC           glBufferSubData;
PFNGLDELETEBUFFERSPROC           glDeleteBuffers;
PFNGLVERTEXATTRIBPOINTERPROC     glVertexAttribPointer;
PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;
PFNGLCREATESHADERPROC            glCreateShader;
PFNGLSHADERSOURCEPROC            glShaderSource;
PFNGLCOMPILESHADERPROC           glCompileShader;
PFNGLGETSHADERIVPROC             glGetShaderiv;
PFNGLGETSHADERINFOLOGPROC        glGetShaderInfoLog;
PFNGLDELETESHADERPROC            glDeleteShader;
PFNGLCREATEPROGRAMPROC           glCreateProgram;
PFNGLATTACHSHADERPROC            glAttachShader;
PFNGLLINKPROGRAMPROC             glLinkProgram;
PFNGLGETPROGRAMIVPROC            glGetProgramiv;
PFNGLGETPROGRAMINFOLOGPROC       glGetProgramInfoLog;
PFNGLUSEPROGRAMPROC              glUseProgram;
PFNGLDELETEPROGRAMPROC           glDeleteProgram;
PFNGLGETUNIFORMLOCATIONPROC      glGetUniformLocation;
PFNGLUNIFORM1FPROC               glUniform1f;
PFNGLUNIFORM1IPROC               glUniform1i;
PFNGLUNIFORM3FPROC               glUniform3f;
PFNGLUNIFORM3FVPROC              glUniform3fv;
PFNGLUNIFORM4FVPROC              glUniform4fv;
PFNGLUNIFORMMATRIX4FVPROC        glUniformMatrix4fv;
#endif
