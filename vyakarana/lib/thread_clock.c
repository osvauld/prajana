/* thread_clock.c — per-thread CPU time via CLOCK_THREAD_CPUTIME_ID */
#include <time.h>
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>

CAMLprim value caml_thread_cpu_us(value unit) {
    CAMLparam1(unit);
    struct timespec ts;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
    double us = (double)ts.tv_sec * 1e6 + (double)ts.tv_nsec / 1e3;
    CAMLreturn(caml_copy_double(us));
}
