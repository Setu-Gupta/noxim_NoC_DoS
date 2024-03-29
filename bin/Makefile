##### LIBRARIES CONFIGURATION #####

# SYSTEMC := /usr/local/systemc-2.3.1
SYSTEMC := /home/anonymous/noxim/systemC/2.3.1-debug/systemc-2.3.1a
YAML    := /home/anonymous/noxim/yaml/yaml-cpp


##### DIRECTORIES #####

SYSTEMC_LIBS := $(wildcard $(SYSTEMC)/lib-*)

SRCDIR  := ../src
SUBDIRS := $(filter %/,$(wildcard $(SRCDIR)/*/))
OBJDIR  := ./build

SRCS := $(wildcard $(SRCDIR)/*.cpp) $(wildcard $(addsuffix *.cpp,$(SUBDIRS)))
OBJS := $(subst $(SRCDIR),$(OBJDIR),$(SRCS:.cpp=.o))

# Generate dependency files
DEPS := $(OBJS:%.o=%.d)

MODULE := noxim


##### COMPILER OPTIONS #####

CXX      := g++
OPT      := -O3
# to enable logs with LOG macro, uncomment "-g DDEBUG" in the line below
# and recompile everythin (make clean)
DEBUG    :=  -g -DDEBUG
OTHER    := -Wall -DSC_NO_WRITE_CHECK --std=c++11 # -Wno-deprecated
CXXFLAGS := $(OPT) $(OTHER) $(DEBUG)

INCDIR := -I$(SRCDIR) -isystem $(SYSTEMC)/include -I$(YAML)/include
LIBDIR := -L$(SRCDIR) -L$(SYSTEMC_LIBS) -L$(YAML)/lib

LIBS := -lsystemc -lm -lyaml-cpp 

SPACE := $(subst ,, )
VPATH := $(SRCDIR):$(subst $(SPACE),:,$(SUBDIRS))




##### RULES #####

$(MODULE): $(OBJS)
	$(CXX) $(LIBDIR) $^ $(LIBS) -o $@ 2>&1 | c++filt

-include Makefile.deps $(DEPS)

$(OBJDIR)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCDIR) -MMD -c $< -o $@

clean:
	rm -f $(OBJS) $(MODULE) $(DEPS) *~

depend: 
	makedepend $(SRCS) -Y -f- 2>/dev/null | sed 's_$(SRCDIR)_$(OBJDIR)_' > Makefile.deps

