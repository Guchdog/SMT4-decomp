#pragma once

#ifndef INFINITY
#define INFINITY (__builtin_inff())
#endif

#ifndef NAN
#define NAN (__builtin_nanf(""))
#endif

#ifdef __cplusplus
extern "C" {
#endif

float sinf(float arg);
float cosf(float arg);
float tanf(float arg);
float asinf(float arg);
float acosf(float arg);
float atan2f(float y, float x);
float sqrtf(float arg);
float fabsf(float arg);
float floorf(float arg);
float ceilf(float arg);
float fmodf(float x, float y);
float powf(float base, float exp);
float fmaxf(float x, float y);
float fminf(float x, float y);

double sin(double arg);
double cos(double arg);
double sqrt(double arg);
double fabs(double arg);
double floor(double arg);
double ceil(double arg);
double fmax(double x, double y);
double fmin(double x, double y);
double fmod(double x, double y);
double pow(double base, double exp);

#ifdef __cplusplus
}
#endif
