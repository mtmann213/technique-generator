find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_TECHNIQUEMAKER gnuradio-techniquemaker)

FIND_PATH(
    GR_TECHNIQUEMAKER_INCLUDE_DIRS
    NAMES gnuradio/techniquemaker/api.h
    HINTS $ENV{TECHNIQUEMAKER_DIR}/include
        ${PC_TECHNIQUEMAKER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_TECHNIQUEMAKER_LIBRARIES
    NAMES gnuradio-techniquemaker
    HINTS $ENV{TECHNIQUEMAKER_DIR}/lib
        ${PC_TECHNIQUEMAKER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-techniquemakerTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_TECHNIQUEMAKER DEFAULT_MSG GR_TECHNIQUEMAKER_LIBRARIES GR_TECHNIQUEMAKER_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_TECHNIQUEMAKER_LIBRARIES GR_TECHNIQUEMAKER_INCLUDE_DIRS)
