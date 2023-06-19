import types
import sys
from ainodes_frontend import singleton as gs
from ainodes_frontend.base import register_node, AiNode, register_node_now, get_next_opcode
from ainodes_frontend.node_engine.node_content_widget import QDMNodeContentWidget

# Create a dummy module
comfy = types.ModuleType('comfy')
comfy.clip_vision = types.ModuleType('comfy.clip_vision')
comfy.clip_vision.encode = lambda: print('Dummy function called')

# Define the dummy function
def dummy_fn():
    print('Dummy function called')


def get_filename_list(path):
    return []

def get_folder_paths(path):
    return []
# Assign the dummy function to comfy.clip_vision.diffusers_convert
comfy.diffusers_convert = dummy_fn

from custom_nodes.ainodes_engine_base_nodes.ainodes_backend import samplers, pixmap_to_pil_image, pil_image_to_pixmap

comfy.samplers = samplers
comfy.sd = dummy_fn
comfy.utils = dummy_fn
comfy.model_management = dummy_fn
folder_paths = types.ModuleType('folder_paths')

folder_paths.folder_names_and_paths = {}
folder_paths.folder_names_and_paths["custom_nodes"] = [["custom_nodes/ainodes_engine_comfy_nodes/src/was_nodes"]]
folder_paths.models_dir = gs.checkpoints

folder_paths.get_filename_list = get_filename_list
folder_paths.get_folder_paths = get_folder_paths

model_management = types.ModuleType('model_management')
comfy_extras = types.ModuleType('comfy_extras')
comfy_extras.chainner_models = types.ModuleType('comfy_extras.chainner_models')
comfy_extras.chainner_models.model_loading = dummy_fn
nodes = types.ModuleType('nodes')

# Add the dummy module to sys.modules
sys.modules['comfy.clip_vision'] = comfy.clip_vision
sys.modules['comfy.diffusers_convert'] = comfy.diffusers_convert
sys.modules['comfy.samplers'] = comfy.samplers
sys.modules['comfy.sd'] = comfy.sd
sys.modules['comfy.utils'] = comfy.utils
sys.modules['comfy'] = comfy
sys.modules['folder_paths'] = folder_paths
sys.modules['model_management'] = model_management
sys.modules['comfy_extras'] = comfy_extras
sys.modules['comfy_extras.chainner_models'] = comfy_extras.chainner_models
sys.modules['comfy_extras.chainner_models.model_loading'] = comfy_extras.chainner_models.model_loading
sys.modules['nodes'] = nodes


defaults = {"FLOAT":{"min":0.0,
                     "max":100.0,
                     "default":1.0,
                     "step":0.01},
            "INT":  {"min":0,
                     "max":100,
                     "default":1,
                     "step":1},
            "NUMBER":  {"min":0,
                     "max":1,
                     "default":1,
                     "step":1},
            }

def create_node(node_class, node_name, ordered_inputs, inputs, ordered_outputs, outputs, fn):

    input_names = ordered_inputs.pop(len(ordered_inputs) - 1)
    output_names = ordered_outputs.pop(len(ordered_outputs) - 1)


    print("INPUT NAMES BECAME", input_names)

    class_name = node_name.replace(" ", "")
    #class_code = "OP_NODE_" + class_name.upper()
    class_code = get_next_opcode()

    # Create new Widget class
    class Widget(QDMNodeContentWidget):
        def initUI(self):

            self.input_adapted = []
            height = 0
            for input_item in ordered_inputs:

                #print("INPUT ITEM", input_item)

                tp = input_item[1][0]
                if type(tp) == str:
                    source = input_item[1]

                    if tp in ['FLOAT', 'INT', 'NUMBER']:
                        min_val = defaults[tp]['min']
                        max_val = defaults[tp]['max']
                        def_val = defaults[tp]['default']
                        step_val = defaults[tp]['step']
                        #print("SOURCE", source)
                        if len(list(source)) > 1:
                            if 'min' in source[1]:
                                min_val = source[1]['min']
                            if 'max' in source[1]:
                                max_val = source[1]['max']
                            if 'default' in source[1]:
                                def_val = source[1]['default']
                            if 'step' in source[1]:
                                step_val = source[1]['step']
                        if min_val < -2147483648:
                            min_val = -2147483647
                        if max_val > 2147483647:
                            max_val = 2147483647
                        if tp == 'FLOAT':
                            setattr(self, input_item[0], self.create_double_spin_box(label_text=input_item[0], min_val=min_val, max_val=max_val, step=step_val, default_val=def_val))
                        elif tp in ['INT', 'NUMBER']:
                            setattr(self, input_item[0], self.create_spin_box(label_text=input_item[0], min_val=int(min_val), max_val=int(max_val), step_value=int(step_val), default_val=int(def_val)))
                        height += 50
                    elif tp in ['STRING', 'CROP_DATA', 'IMAGE_BOUNDS', 'PROMPT']:


                        default = 'default_placeholder'
                        multiline = False
                        if len(list(source)) > 1:
                            if 'multiline' in source[1]:
                                multiline = source[1]['multiline']
                            if 'default' in source[1]:
                                default = source[1]['default']
                        if tp == 'PROMPT':
                            multiline = True
                            default = "Prompt"
                        if multiline:
                            setattr(self, input_item[0], self.create_text_edit(input_item[0], placeholder=default))
                            tp = 'MULTI_STRING'
                            height += 100

                        else:
                            setattr(self, input_item[0], self.create_line_edit(input_item[0], default=default, placeholder=default))
                            height += 50

                    self.input_adapted.append({"type":tp,
                                               "name":input_item[0]})



                elif type(tp) == list:

                    setattr(self, input_item[0],
                            self.create_combo_box(input_item[1][0], input_item[0], accessible_name=input_item[0]))
                    self.input_adapted.append({"type":"COMBOBOX",
                                               "name":input_item[0]})
                    height += 50

            self.create_main_layout(grid=1)
            self.setMinimumHeight(height)
            self.setMaximumHeight(height)


    # Create new Node class
    class Node(AiNode, node_class):
        icon = "ainodes_frontend/icons/base_nodes/v2/experimental.png"
        help_text = "Data objects in aiNodes are simple dictionaries,\n" \
                    "that can hold any values under any name.\n" \
                    "In most cases, you'll find them drive parameters,\n" \
                    "or hold sequences of images. For an example, the\n" \
                    "OpenAI node emits it's prompt in a data line,\n" \
                    "but you'll find this info in all relevant places."
        op_code = class_code
        op_title = node_name
        content_label_objname = class_name.lower().replace(" ", "_")
        category = "WAS NODES"
        NodeContent_class = Widget
        dim = (340, 180)
        output_data_ports = outputs
        exec_port = 0

        custom_input_socket_name = input_names
        custom_output_socket_name = output_names

        def __init__(self, scene):
            super().__init__(scene, inputs=inputs, outputs=outputs)

            self.fn = fn
            self.ordered_outputs = ordered_outputs

            self.exec_port = len(self.outputs) - 1

            modifier = len(inputs)
            if len(outputs) > len(inputs):
                modifier = len(outputs)

            self.grNode.height = 125 + self.content.minimumHeight() + (40 * modifier)

            self.update_all_sockets()

        def evalImplementation_thread(self):
            from .src.was_nodes.WAS_Node_Suite import pil2tensor, tensor2pil

            data_inputs = []
            x = 0
            for adapted_input in self.content.input_adapted:
                data = f"Not Found {adapted_input['name']}"
                if adapted_input['type'] in ['LATENT', 'IMAGE', 'CONDITIONING', 'EXTRA_PNGINFO']:
                    data = self.getInputData(x)
                    x += 1
                    if adapted_input['type'] == 'IMAGE':
                        data = pixmap_to_pil_image(data[0])
                        data = pil2tensor(data)
                elif adapted_input['type'] in ['FLOAT', 'INT']:
                    data = getattr(self.content, adapted_input['name']).value()
                elif adapted_input['type'] == 'STRING':
                    data = getattr(self.content, adapted_input['name']).text()
                elif adapted_input['type'] == 'MULTI_STRING':
                    data = getattr(self.content, adapted_input['name']).toPlainText()
                elif adapted_input['type'] in ['CROP_DATA', 'IMAGE_BOUNDS']:
                    data = getattr(self.content, adapted_input['name']).text()
                    data = data.split(",")
                    data = tuple(int(item) for item in data)
                elif adapted_input['type'] == 'COMBOBOX':
                    data = getattr(self.content, adapted_input['name']).currentText()
                data_inputs.append(data)

            # for i in range(len(self.inputs)):
            #     data = self.getInputData(x)
            #     data_inputs.append(data)
            #     x += 1
            #     print(x)

            print(data_inputs)
            result = self.fn(self, *data_inputs)
            x = 0
            for output in self.ordered_outputs:
                if output['type'] == 'IMAGE':
                    image = result[x]
                    pil = tensor2pil(image)
                    self.setOutput(x, [pil_image_to_pixmap(pil)])


            print(result)


    # Register the node
    register_node_now(class_code, Node)

    # Store the node in node class mapping
    #node_class_map[node_name] = Node
# Import other modules that depend on comfy.clip_vision
from .src.was_nodes import WAS_Node_Suite

#print("WAS INIT", WAS_Node_Suite.NODE_CLASS_MAPPINGS)


def get_node_parameters(node_class):

    ordered_inputs = []

    for key, value in node_class.INPUT_TYPES().items():
        for value_name, value_params in value.items():

            print("VALUE", value_name, value_params)

            ordered_inputs.append((value_name, value_params))

    return ordered_inputs



for node_name, node_class in WAS_Node_Suite.NODE_CLASS_MAPPINGS.items():

    #print(node_name.lower().replace(" ", "_"))

    node_content_class = node_name.lower().replace(" ", "_")

    #print(node_class.INPUT_TYPES())

    ordered_inputs = get_node_parameters(node_class)

    inputs = []
    input_names = []
    outputs = []
    for i in ordered_inputs:
        if i[1][0] == "LATENT":
            inputs.append(2)
        elif i[1][0] in ["IMAGE", "MASK"]:
            inputs.append(5)
        elif i[1][0] == "CONDITIONING":
            inputs.append(3)
        elif i[1][0] in ["EXTRA_PNGINFO"]:
            inputs.append(6)
        elif i[1][0] in ["VAE", "CLIP", "MODEL"]:
            inputs.append(4)
        if i[1][0] in ["LATENT", "IMAGE", "MASK", "CONDITIONING", "EXTRA_PNGINFO", "VAE", "CLIP", "MODEL"]:
            input_names.append(i[1][0])
    input_names.append("EXEC")
    ordered_inputs.append(input_names)
        # elif i[1][0] == "IMAGE_BOUNDS":
        #     inputs.append(6)
    #print("RESULT INPUTS", inputs)

    fn = getattr(node_class, node_class.FUNCTION)
    ordered_outputs = []
    output_names = []
    x = 0
    for i in node_class.RETURN_TYPES:
        data = {}
        data['type'] = i
        data['name'] = "DEFAULT"
        if hasattr(node_class, "RETURN_NAMES"):
            data['name'] = node_class.RETURN_NAMES[x]
        if i in ["STRING", "NUMBER"]:
            outputs.append(6)
        elif i == "LATENT":
            outputs.append(2)
        elif i == "IMAGE":
            outputs.append(5)
        elif i == "CONDITIONING":
            outputs.append(3)
        elif i in ["VAE", "CLIP", "MODEL"]:
            outputs.append(4)
        if i in ["LATENT", "IMAGE", "MASK", "CONDITIONING", "EXTRA_PNGINFO", "VAE", "CLIP", "MODEL", "STRING", "NUMBER"]:
            output_names.append(i)


        ordered_outputs.append(data)
    output_names.append('EXEC')

    ordered_outputs.append(output_names)
    outputs.append(1)
    inputs.append(1)
    # Use the function
    create_node(node_class, node_name, ordered_inputs, inputs, ordered_outputs, outputs, fn=fn)


# test_subject = list(WAS_Node_Suite.NODE_CLASS_MAPPINGS.values())[0]
#
# print(test_subject.INPUT_TYPES())






