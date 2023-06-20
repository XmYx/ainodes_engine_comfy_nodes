import numpy as np
import torch
from PIL import Image

from ai_nodes.ainodes_engine_base_nodes.ainodes_backend import pixmap_to_pil_image, pil_image_to_pixmap

loadBackup = torch.load

#from . import install_all_comfy_nodes


from ainodes_frontend.base import register_node, AiNode, register_node_now, get_next_opcode
from ainodes_frontend.node_engine.node_content_widget import QDMNodeContentWidget


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


def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# PIL to Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def create_node(node_class, node_name, ordered_inputs, inputs, ordered_outputs, outputs, fn):

    input_names = ordered_inputs.pop(len(ordered_inputs) - 1)
    output_names = ordered_outputs.pop(len(ordered_outputs) - 1)


    #print("INPUT NAMES BECAME", input_names)

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
                            setattr(self, input_item[0], self.create_text_edit(input_item[0], default=default))
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
            print("ADAPTED INPUT LIST", self.input_adapted)
            self.create_main_layout(grid=1)
            #self.setMinimumHeight(height)
            #self.setMaximumHeight(height)


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
        category = f"ComfyUI_Extras/{node_class.CATEGORY}"#"WAS NODES"
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

            self.content.setGeometry(0, 15, self.content.geometry().width(), self.content.geometry().height())

            self.grNode.height = self.content.geometry().height() + (modifier * 30)

            self.update_all_sockets()

        def evalImplementation_thread(self):

            data_inputs = {}
            x = 0
            for adapted_input in self.content.input_adapted:
                data = f"Not Found {adapted_input['name']}"
                if adapted_input['type'] in ['LATENT', 'IMAGE', 'CONDITIONING', 'EXTRA_PNGINFO', "VAE", "CLIP", "MODEL", "GUIDED_DIFFUSION_MODEL", "GUIDED_CLIP", "EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"]:
                    input_data = self.getInputData(x)
                    data = input_data
                    x += 1
                if adapted_input['type'] == 'IMAGE':
                    if input_data is not None:
                        input_data = pixmap_to_pil_image(input_data[0])
                        data = pil2tensor(input_data)
                elif adapted_input['type'] in ["EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"] and input_data == None:
                    data = {}
                elif adapted_input['type'] == ["LATENT"]:
                    data = {"samples":input_data[0]}
                elif adapted_input['type'] == ["CONDITIONING"]:
                    data = input_data[0]
                elif adapted_input['type'] in ['FLOAT', 'INT']:
                    data = getattr(self.content, adapted_input['name']).value()
                elif adapted_input['type'] == 'STRING':
                    data = getattr(self.content, adapted_input['name']).text()
                elif adapted_input['type'] in ['MULTI_STRING', 'PROMPT']:
                    data = getattr(self.content, adapted_input['name']).toPlainText()
                elif adapted_input['type'] in ['CROP_DATA', 'IMAGE_BOUNDS']:
                    data = getattr(self.content, adapted_input['name']).text()
                    data = data.split(",")
                    data = tuple(int(item) for item in data)
                elif adapted_input['type'] == 'COMBOBOX':
                    data = getattr(self.content, adapted_input['name']).currentText()
                if adapted_input['name'] in ["latent_image"]:
                    data_inputs[adapted_input['name']] = {"samples":data[0]}
                elif adapted_input['name'] in ["samples"]:
                    data_inputs[adapted_input['name']] = {"samples":data}
                elif adapted_input['name'] in ['positive', 'negative']:
                    data_inputs[adapted_input['name']] = data[0]
                else:
                    data_inputs[adapted_input['name']] = data

            # for i in range(len(self.inputs)):
            #     data = self.getInputData(x)
            #     data_inputs.append(data)
            #     x += 1
            #     print(x)

            #print(data_inputs)

            print("COLLECTED COMFY INPUTS", data_inputs)

            result = self.fn(self, **data_inputs)
            x = 0
            pixmaps = []
            for output in self.ordered_outputs:
                if output['type'] == 'IMAGE':
                    image = result[x]
                    if isinstance(image, list):
                        for img in image:
                            img = img.detach().cpu()
                            pil = tensor2pil(img)
                            pixmaps.append(pil_image_to_pixmap(pil))
                    else:
                        image = image.detach().cpu()
                        pil = tensor2pil(image)
                        pixmaps = [pil_image_to_pixmap(pil)]
                    self.setOutput(x, pixmaps)
                elif output['type'] == 'LATENT':
                    if isinstance(result[x], dict):
                        samples = result[x]["samples"].detach().cpu()
                    elif isinstance(result[x], list):
                        samples = result[x][0].detach().cpu()
                    else:
                        samples = result[x].detach().cpu()
                    self.setOutput(x, samples)
                else:
                    self.setOutput(x, result[x])
            print("RAN COMFY NODE", self.op_title, "in aiNodes Engine")



    # Register the node
    register_node_now(class_code, Node)



def get_node_parameters(node_class):

    ordered_inputs = []

    for key, value in node_class.INPUT_TYPES().items():
        for value_name, value_params in value.items():



            ordered_inputs.append((value_name, value_params))

    return ordered_inputs


def parse_comfynode(node_name, node_class):
    node_content_class = node_name.lower().replace(" ", "_")

    # print(node_class.INPUT_TYPES())
    try:
        ordered_inputs = get_node_parameters(node_class)

        # print("ORDERED INPUTS #1", ordered_inputs)

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
            elif i[1][0] in ["EXTRA_PNGINFO", "EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"]:
                inputs.append(6)
            elif i[1][0] in ["VAE", "CLIP", "MODEL", "GUIDED_DIFFUSION_MODEL", "GUIDED_CLIP"]:
                inputs.append(4)
            if i[1][0] in ["LATENT", "IMAGE", "MASK", "CONDITIONING", "EXTRA_PNGINFO", "VAE", "CLIP", "MODEL", "GUIDED_DIFFUSION_MODEL", "GUIDED_CLIP", "EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"]:
                input_names.append(i[1][0])
        input_names.append("EXEC")
        ordered_inputs.append(input_names)
        # elif i[1][0] == "IMAGE_BOUNDS":
        #     inputs.append(6)
        # print("RESULT INPUTS", inputs)

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
            if i in ["STRING", "NUMBER", "EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"]:
                outputs.append(6)
            elif i == "LATENT":
                outputs.append(2)
            elif i in ["IMAGE", "MASK"]:
                outputs.append(5)
            elif i == "CONDITIONING":
                outputs.append(3)
            elif i in ["VAE", "CLIP", "MODEL", "GUIDED_DIFFUSION_MODEL", "GUIDED_CLIP"]:
                outputs.append(4)
            if i in ["LATENT", "IMAGE", "MASK", "MASKS", "CONDITIONING", "EXTRA_PNGINFO", "VAE", "CLIP", "MODEL", "GUIDED_DIFFUSION_MODEL", "GUIDED_CLIP",
                     "STRING", "NUMBER", "EXTRA_SETTINGS", "DISCO_DIFFUSION_EXTRA_SETTINGS"]:
                output_names.append(i)
            ordered_outputs.append(data)
        output_names.append('EXEC')

        # print("CREATED OUTPUT NAMES", output_names)

        ordered_outputs.append(output_names)
        outputs.append(1)
        inputs.append(1)
        # Use the function
        create_node(node_class, node_name, ordered_inputs, inputs, ordered_outputs, outputs, fn=fn)
    except:
        pass
