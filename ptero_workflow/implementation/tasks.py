from . import exceptions
from . import models


def build_task(name, data, parent_method=None):
    task = models.MethodList(name=name,
            parallel_by=data.get('parallelBy'),
            parent=parent_method)

    for index, method_data in enumerate(data.get('methods', [])):
        task.method_list.append(build_method(method_data, index=index,
            parent_task=task))

    return task


def build_method(data, index=None, parent_task=None):
    if 'tasks' in data:
        return _build_dag_method(data, index, parent_task)
    elif 'service' in data:
        return _build_service_method(data, index, parent_task,
                models.SUBCLASS_LOOKUP[data['service']])
    raise RuntimeError('No method found for class')


def _build_dag_method(data, index, parent_task):
    _validate_dag_data(data)

    method = models.DAGMethod(name=data.get('name'), index=index,
            task=parent_task)

    children = {}
    for name, child_task_data in data['tasks'].iteritems():
        children[name] = build_task(name, child_task_data,
                parent_method=method)
    children['input connector'] = models.InputConnector(
        name='input connector', parent=method)
    children['output connector'] = models.OutputConnector(
        name='output connector', parent=method)

    method.children = children

    for link_data in data['links']:
        source = children[link_data['source']]
        destination = children[link_data['destination']]
        models.Link(
            destination_task=destination,
            destination_property=link_data['destinationProperty'],
            source_task=source,
            source_property=link_data['sourceProperty'],
        )

    return method


def _build_service_method(data, index, parent_task, cls):
    return cls(name=data.get('name'), index=index, task=parent_task,
            parameters=data.get('parameters', {}))


def create_input_holder(root, inputs, color):
    task = models.InputHolder(name='input_holder')
    task.set_outputs(inputs, color=color, parent_color=None)
    for i in inputs.iterkeys():
        models.Link(source_task=task, destination_task=root,
                source_property=i, destination_property=i)
    return task


def _validate_dag_data(data):
    _validate_dag_task_names(data['tasks'])


_ILLEGAL_TASK_NAMES = {'input connector', 'output connector'}


def _validate_dag_task_names(tasks):
    for illegal_name in _ILLEGAL_TASK_NAMES:
        if illegal_name in tasks:
            raise exceptions.InvalidWorkflow('"%s" is an illegal task name'
                    % illegal_name)
