# SPDX-License-Identifier: LGPL-2.1-or-later
# ==============================================================================
# Arxio AI workbench - build definition.
#
# The workbench is Python-only: no native (C++) dependencies are required.
# CMake is used solely to copy Python sources and resources (SVG icons,
# translations, package manifest) to the build/install tree so the workbench
# can be loaded at runtime by FreeCAD.
# ==============================================================================

SET(Arxio_SRCS
    Init.py
    InitGui.py
    ArxioUtils.py
    ArxioCommands.py
    ArxioTaskPanels.py
    ArxioHouseBuilder.py
    ArxioExporters.py
)

SET(Arxio_Icons
    Resources/icons/ArxioWorkbench.svg
    Resources/icons/Arxio_PresetHouse.svg
    Resources/icons/Arxio_FastWalls.svg
    Resources/icons/Arxio_SmartOpenings.svg
    Resources/icons/Arxio_AutoRoof.svg
    Resources/icons/Arxio_Estimate.svg
    Resources/icons/Arxio_SunStudy.svg
    Resources/icons/Arxio_AutoPlan.svg
    Resources/icons/Arxio_ExportPDF.svg
    Resources/icons/Arxio_Welcome.svg
    Resources/icons/Arxio_About.svg
)

SET(Arxio_Tests
    tests/__init__.py
    tests/TestArxio.py
)

SET(Arxio_Manifest
    package.xml
)

SET(Arxio_All
    ${Arxio_SRCS}
    ${Arxio_Icons}
    ${Arxio_Tests}
    ${Arxio_Manifest}
)

SOURCE_GROUP("" FILES ${Arxio_SRCS})
SOURCE_GROUP("icons" FILES ${Arxio_Icons})
SOURCE_GROUP("tests" FILES ${Arxio_Tests})

ADD_CUSTOM_TARGET(Arxio ALL
    SOURCES ${Arxio_All}
)

# Populate the build tree with Python sources and test payload
fc_copy_sources(Arxio "${CMAKE_BINARY_DIR}/Mod/Arxio" ${Arxio_SRCS})
fc_copy_sources(Arxio "${CMAKE_BINARY_DIR}/Mod/Arxio" ${Arxio_Tests})
fc_copy_sources(Arxio "${CMAKE_BINARY_DIR}/Mod/Arxio" ${Arxio_Manifest})

# Populate the resource side of the build tree (icons live under Resources)
fc_copy_sources(Arxio "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_DATADIR}/Mod/Arxio"
    ${Arxio_Icons})

# ==============================================================================
# Install
# ==============================================================================

INSTALL(
    FILES ${Arxio_SRCS}
    DESTINATION Mod/Arxio
)

INSTALL(
    FILES ${Arxio_Manifest}
    DESTINATION Mod/Arxio
)

INSTALL(
    FILES ${Arxio_Tests}
    DESTINATION Mod/Arxio/tests
)

INSTALL(
    FILES ${Arxio_Icons}
    DESTINATION "${CMAKE_INSTALL_DATADIR}/Mod/Arxio/Resources/icons"
)
