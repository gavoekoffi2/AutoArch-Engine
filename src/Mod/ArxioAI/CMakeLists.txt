# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Arxio AI workbench — pure-Python module.
# Built on FreeCAD (LGPL-2.1-or-later).

set(ArxioAI_PY
    Init.py
    InitGui.py
    __init__.py
    ArxioAICommands.py
)

set(ArxioAITools_PY
    ArxioAITools/__init__.py
    ArxioAITools/project.py
    ArxioAITools/walls.py
    ArxioAITools/roof.py
    ArxioAITools/openings.py
    ArxioAITools/plan.py
    ArxioAITools/estimate.py
)

set(ArxioAI_Icons
    Resources/icons/ArxioAIWorkbench.svg
    Resources/icons/ArxioAI_SetupProject.svg
    Resources/icons/ArxioAI_FastWalls.svg
    Resources/icons/ArxioAI_AutoRoof.svg
    Resources/icons/ArxioAI_Openings.svg
    Resources/icons/ArxioAI_AutoPlan.svg
    Resources/icons/ArxioAI_Estimate.svg
)

# Copy to build tree so the workbench is usable without installing.
foreach(f ${ArxioAI_PY})
    configure_file(${f} ${CMAKE_CURRENT_BINARY_DIR}/${f} COPYONLY)
endforeach()
foreach(f ${ArxioAITools_PY})
    configure_file(${f} ${CMAKE_CURRENT_BINARY_DIR}/${f} COPYONLY)
endforeach()
foreach(f ${ArxioAI_Icons})
    configure_file(${f} ${CMAKE_CURRENT_BINARY_DIR}/${f} COPYONLY)
endforeach()

# Install to the FreeCAD Mod layout.
set(_dst Mod/ArxioAI)
install(FILES ${ArxioAI_PY} DESTINATION ${_dst})
install(FILES ${ArxioAITools_PY} DESTINATION ${_dst}/ArxioAITools)
install(FILES ${ArxioAI_Icons} DESTINATION ${_dst}/Resources/icons)

# Register as a FreeCAD source group for IDEs.
SET(all_files
    ${ArxioAI_PY}
    ${ArxioAITools_PY}
    ${ArxioAI_Icons}
)
ADD_CUSTOM_TARGET(ArxioAI ALL SOURCES ${all_files})
