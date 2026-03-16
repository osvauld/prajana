# Makefile — vyakarana render (standalone C proof of concept)
#
# SDL2 + OpenGL 3.3 core profile, no GLAD/GLEW
# Build: make
# Run:   ./render

CC      = gcc
CFLAGS  = -std=c11 -O2 -Wall -Wextra \
          $(shell pkg-config --cflags sdl2) \
          -I/usr/include/GL
LIBS    = $(shell pkg-config --libs sdl2) -lGL -lm

TARGET  = render
SRC     = main.c

$(TARGET): $(SRC) gl.h vert.glsl frag.glsl
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LIBS)

clean:
	rm -f $(TARGET)

.PHONY: clean
