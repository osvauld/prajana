#version 330 core

/* fragment shader — pbr: light-ahara, color-phala, energy-siddha
 *
 * Cook-Torrance BRDF. Implements what pbr.om says:
 *   pbr — material-swarupa, energy-siddha, photon-abheda, light-ahara, color-phala
 *
 * The three terms (D, F, G) together ensure energy conservation (energy-siddha):
 *   D — normal distribution function (GGX): how much surface area faces the light
 *   F — Fresnel (Schlick): how much light reflects vs refracts at this angle
 *   G — geometry/shadowing (Smith): microfacets occluding each other
 *
 * f(l,v) = (D × F × G) / (4 × NdotL × NdotV)
 *
 * Kosha:
 *   pbr        — energy-siddha, photon-abheda, light-ahara, color-phala
 *   material   — roughness-yukta, metallic-yukta, albedo-yukta
 *   light      — photon-abheda, energy-sthita, position-yukta, color-yukta
 *   fragment   — tala-sthita, rasterization-janya (born from rasterization)
 */

in vec3 v_world_pos;
in vec3 v_normal;
in vec2 v_uv;

/* material (material-swarupa, pbr-sthita) */
uniform vec3  u_albedo;      /* base color */
uniform float u_roughness;   /* 0=mirror, 1=fully rough */
uniform float u_metallic;    /* 0=dielectric, 1=metal */

/* light (photon-abheda, energy-sthita, position-yukta) */
uniform vec3  u_light_pos;
uniform vec3  u_light_color;

/* camera (darshana-swarupa) */
uniform vec3  u_cam_pos;

out vec4 frag_color;

const float PI = 3.14159265359;

/* D — GGX normal distribution: concentration of microfacets aligned to H */
float D_GGX(vec3 N, vec3 H, float roughness) {
    float a  = roughness * roughness;
    float a2 = a * a;
    float NdotH  = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    float denom = NdotH2 * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

/* G — Smith geometry: microfacet self-shadowing */
float G_schlick(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}
float G_smith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    return G_schlick(NdotV, roughness) * G_schlick(NdotL, roughness);
}

/* F — Fresnel-Schlick: reflectance at grazing angles */
vec3 F_schlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main() {
    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);
    vec3 L = normalize(u_light_pos - v_world_pos);
    vec3 H = normalize(V + L);

    /* F0: base reflectance. metals use albedo, dielectrics use 0.04 */
    vec3 F0 = mix(vec3(0.04), u_albedo, u_metallic);

    float NdotL = max(dot(N, L), 0.0);
    float dist  = length(u_light_pos - v_world_pos);
    vec3  radiance = u_light_color * (1.0 / (dist * dist));

    /* Cook-Torrance specular: D × F × G / (4 × NdotL × NdotV) */
    float D = D_GGX(N, H, u_roughness);
    vec3  F = F_schlick(max(dot(H, V), 0.0), F0);
    float G = G_smith(N, V, L, u_roughness);

    float NdotV = max(dot(N, V), 0.0);
    vec3 specular = (D * F * G) / max(4.0 * NdotL * NdotV, 0.001);

    /* diffuse: metals absorb all refracted light (kSpecular = F) */
    vec3 kD = (vec3(1.0) - F) * (1.0 - u_metallic);
    vec3 diffuse = kD * u_albedo / PI;

    /* final color: energy-siddha (energy is conserved in diffuse+specular) */
    vec3 Lo = (diffuse + specular) * radiance * NdotL;

    /* ambient: small constant term so nothing goes fully black */
    vec3 ambient = vec3(0.03) * u_albedo;
    vec3 color   = ambient + Lo;

    /* tone-map (Reinhard) + gamma correction */
    color = color / (color + vec3(1.0));
    color = pow(color, vec3(1.0 / 2.2));

    frag_color = vec4(color, 1.0);
}
