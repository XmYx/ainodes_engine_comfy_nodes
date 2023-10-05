import importlib
import inspect

from ai_nodes.ainodes_engine_comfy_nodes.adapter_nodes.adapter_utils import create_node

# Dynamically import the diffusers.pipelines module
pipelines_module = importlib.import_module("diffusers.pipelines")

pipeline_classes = []

# Loop through all members of the pipelines module
for name, obj in inspect.getmembers(pipelines_module):
    # Check if the member is a class and has "Pipeline" in its name
    if inspect.isclass(obj) and "Pipeline" in name:

        # Extract the __call__ method's parameters
        call_method = getattr(obj, "__call__", None)
        if call_method:
            signature = inspect.signature(call_method)
            params = signature.parameters
            param_info = []

            for param_name, param in params.items():
                # Skip 'self' parameter
                if param_name == "self":
                    continue

                # Extract parameter details
                param_dict = {
                    "name": param_name,
                    "default": param.default if param.default != param.empty else None,
                    "type": str(param.annotation) if param.annotation != param.empty else None
                }
                param_info.append(param_dict)

            # Extract return type
            return_type = str(signature.return_annotation) if signature.return_annotation != signature.empty else None

            # Create a dictionary for the class
            class_dict = {
                "class_name": name,
                "import_path": f"diffusers.pipelines.{name}",
                "call_parameters": param_info,
                "return_type": return_type
            }
            pipeline_classes.append(class_dict)


def create_node_from_dict(node_dict):
    node_name = node_dict['class_name']
    #node_class = importlib.import_module(node_dict['import_path'])
    node_class = getattr(pipelines_module, node_dict['class_name'])

    call_parameters = node_dict['call_parameters']

    ui_inputs = []
    inputs = []
    input_names = []
    for param in call_parameters:
        param_name = param['name']
        param_type = param['type']
        param_default = param['default']

        if param_type and ("torch.Tensor" in param_type or "PIL.Image.Image" in param_type):
            inputs.append(5)  # default input type for tensors and images
            input_names.append(param_name)
        elif param_type and "<class 'int'>" in param_type:
            ui_type = "INT"
            ui_inputs.append((param_name, (ui_type, {'default': param_default})))
        elif param_type and "<class 'float'>" in param_type:
            ui_type = "FLOAT"
            ui_inputs.append((param_name, (ui_type, {'default': param_default})))
        elif param_type and "<class 'bool'>" in param_type:
            ui_type = "BOOL"
            ui_inputs.append((param_name, (ui_type, {'default': param_default})))
        else:
            ui_type = "STRING"  # default to STRING for other types
            ui_inputs.append((param_name, (ui_type, {'default': param_default})))

    outputs = [1]  # default output type
    output_names = ["EXEC"]
    category_input = "DiffusersAdapted"
    fn = node_class.__call__
    # Use the function
    create_node(node_class, node_name, ui_inputs, inputs, input_names, outputs, output_names, category_input, fn)

def parse_diffusers(node_dict):
    try:
        create_node_from_dict(node_dict)
    except Exception as e:
        print(f"Error creating node for {node_dict['class_name']}: {e}")

# # Print the results
# for pipeline_class in pipeline_classes:
#     parse_diffusers(pipeline_class)
