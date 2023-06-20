#dummy file for comfyui nodes
import glob
import importlib
import time
import traceback

from ai_nodes.ainodes_engine_comfy_nodes.adapter_nodes.adapter_utils import parse_comfynode

WAS = "GREAT"

import os, sys

sys.path.extend([os.path.join(os.getcwd(), "src", "ComfyUI")])


def load_comfy_node(module_path):
    module_name = os.path.basename(module_path)
    if os.path.isfile(module_path):
        sp = os.path.splitext(module_path)
        module_name = sp[0]
    try:
        if os.path.isfile(module_path):
            module_spec = importlib.util.spec_from_file_location(module_name, module_path)
        else:
            module_spec = importlib.util.spec_from_file_location(module_name, os.path.join(module_path, "__init__.py"))
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        module_spec.loader.exec_module(module)
        if hasattr(module, "NODE_CLASS_MAPPINGS") and getattr(module, "NODE_CLASS_MAPPINGS") is not None:

            mappings = getattr(module, "NODE_CLASS_MAPPINGS")

            print("FOUND MAPPING", mappings)

            return mappings

            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
            if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS") and getattr(module, "NODE_DISPLAY_NAME_MAPPINGS") is not None:
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            return True
        else:
            print(f"Skip {module_path} module for custom nodes due to the lack of NODE_CLASS_MAPPINGS.")
            return None
    except Exception as e:
        print(traceback.format_exc())
        print(f"Cannot import {module_path} module for custom nodes:", e)
        return None

def load_comfy_nodes():
    node_paths = [os.path.join(os.getcwd(), "src/ComfyUI/custom_nodes")]

    print("COMFY NODE PATHS", node_paths)
    mappings = []
    node_import_times = []
    for custom_node_path in node_paths:
        possible_modules = os.listdir(custom_node_path)
        if "__pycache__" in possible_modules:
            possible_modules.remove("__pycache__")

        for possible_module in possible_modules:
            module_path = os.path.join(custom_node_path, possible_module)
            if os.path.isfile(module_path) and os.path.splitext(module_path)[1] != ".py": continue
            if module_path.endswith(".disabled"): continue
            time_before = time.perf_counter()
            mapping = load_comfy_node(module_path)
            if mappings is not None:
                mappings.append(mapping)
            node_import_times.append((time.perf_counter() - time_before, module_path, True))

    if len(node_import_times) > 0:
        print("\nImport times for custom nodes:")
        for n in sorted(node_import_times):
            if n[2]:
                import_message = ""
            else:
                import_message = " (IMPORT FAILED)"
            print("{:6.1f} seconds{}:".format(n[0], import_message), n[1])
        print()

    return mappings





directory = "src/ComfyUI/custom_nodes"





import nodes
#from custom_nodes.ComfyUI_Disco_Diffusion.nodes import NODE_CLASS_MAPPINGS

#print("Comfy Node Class Mappings", nodes.NODE_CLASS_MAPPINGS)

node_class_mappings = load_comfy_nodes()

node_class_mappings.append(nodes.NODE_CLASS_MAPPINGS)

for mapping in node_class_mappings:
    if mapping is not None:
        print(mapping)
        for node_name, node_class in mapping.items():
            parse_comfynode(node_name, node_class)