import pandas
from PySide6.QtWidgets import QWidget


from gui.data_configuration.data_filter import DataFilter
from .common.styled_combobox import StyledComboBox
from .common.styled_integer_selector import StyledIntegerSelector
from .picklist_populate_worker import PicklistPopulateWorker

class FieldConfigs:
    '''
    This class is a container for the field configurations for a particular widget.
    It will handle validation of the field configurations to make sure they are valid.
    '''
    def __init__(self, field_configs: dict):
        self._label = field_configs['label']
        self._type = field_configs['type']
        self._default = field_configs['default']
        if 'tooltip' in field_configs:
            self._tooltip = field_configs['tooltip']
        else:
            self._tooltip = None
        if pandas.isnull(field_configs['data_field']):
            self._data_field = None
        else:
            self._data_field = field_configs['data_field']
            if 'select' in self._type:
                if 'display_field' not in field_configs or pandas.isnull(field_configs['display_field']):
                    raise ValueError('For data field ' + str(self._label) + ',' + \
                                    'display_field cannot be null if data_field is not null')
                else:
                    self._display_field = field_configs['display_field']
                if pandas.isnull(field_configs['value_field']):
                    self._value_field = self._display_field
                else:
                    self._value_field = field_configs['value_field']

        if 'validation' not in field_configs or pandas.isnull(field_configs['validation']):
            self._validation = None
        else:
            self._validation = field_configs['validation']
            if self._validation == 'integer':
                if 'minimum' not in field_configs or pandas.isnull(field_configs['minimum']):
                    raise ValueError('For data field ' + str(self._label) + ',' + \
                                     'minimum cannot be null if validation is integer')
                else:
                    self._minimum = field_configs['minimum']
                if 'maximum' not in field_configs or pandas.isnull(field_configs['maximum']):
                    raise ValueError('For data field ' + str(self._label) + ',' + \
                                     'maximum cannot be null if validation is integer')
                else:
                    self._maximum = field_configs['maximum']
            else:
                self._minimum = None
                self._maximum = None
        
        if 'var_name' not in field_configs or pandas.isnull(field_configs['var_name']):
            self._var_name = None
        else:
            self._var_name = field_configs['var_name']

        if "hidden" not in field_configs:
            self._hidden = False
        else:
            self._hidden = field_configs['hidden']

        if "count_field" not in field_configs or pandas.isnull(field_configs['count_field']):
            self._count_field = None
        else:
            self._count_field = field_configs['count_field']

    @property
    def label(self) -> str:
        """This function returns the label for this field.

        Returns:
            str: the label for this field
        """        
        return self._label
    
    @label.setter
    def label(self, value: str):
        """This function sets the label for this field.

        Args:
            value (str): the label for this field
        """   
        self._label = value

    
    @property
    def type(self) -> str:
        """This function returns the type of field this is.

        Returns:
            str: the type of field this is.
        """
        return self._type

    @type.setter
    def type(self, value: str):
        """This function sets the type of field this is.

        Args:
            value (str): the type of field this is.
        """
        if value not in ['single-select', 'multi-select', 'numeric']:
            raise ValueError('Invalid field type: ' + value + ' for data field: ' + self._label + \
                             '. Must be one of: single-select, multi-select, numeric')
        self._type = value

    
    @property
    def tooltip(self) -> str:
        """This function returns the tooltip for this field.

        Returns:
            str: the tooltip for this field
        """        
        return self._tooltip
    
    @tooltip.setter
    def tooltip(self, value: str):
        """This function sets the tooltip for this field.

        Args:
            value (str): the tooltip for this field
        """   
        self._tooltip = value

    
    @property
    def data_field(self) -> str:
        """This function returns the data_field for this field.

        Returns:
            str: the data_field for this field
        """        
        return self._data_field
    
    @data_field.setter
    def data_field(self, value: str):
        """This function sets the data_field for this field.

        Args:
            value (str): the data_field for this field
        """   
        self._data_field = value

    
    @property
    def display_field(self) -> str:
        """This function returns the display_field for this field.

        Returns:
            str: the display_field for this field
        """        
        return self._display_field
    
    @display_field.setter
    def display_field(self, value: str):
        """This function sets the display_field for this field.

        Args:
            value (str): the display_field for this field
        """   
        self._display_field = value


    @property
    def value_field(self) -> str:
        """This function returns the value_field for this field.

        Returns:
            str: the value_field for this field
        """        
        return self._value_field
    
    @value_field.setter
    def value_field(self, value: str):
        """This function sets the value_field for this field.

        Args:
            value (str): the value_field for this field
        """   
        self._value_field = value

    
    @property
    def validation(self) -> str:
        """This function returns the validation for this field.

        Returns:
            str: the validation for this field
        """        
        return self._validation
    
    @validation.setter
    def validation(self, value: str):
        """This function sets the validation for this field.

        Args:
            value (str): the validation for this field
        """   
        if value not in ['integer', 'float']:
            raise ValueError('Invalid validation: ' + value + ' for data field: ' + self._label + \
                             '. Must be one of: [integer, flaot]')
        self._validation = value

    
    @property
    def minimum(self) -> str:
        """This function returns the minimum for this field.

        Returns:
            str: the minimum for this field
        """        
        return self._minimum
    
    @minimum.setter
    def minimum(self, value: str):
        """This function sets the minimum for this field.

        Args:
            value (str): the minimum for this field
        """   
        self._minimum = value


    @property
    def maximum(self) -> str:
        """This function returns the maximum for this field.

        Returns:
            str: the maximum for this field
        """        
        return self._maximum
    
    @maximum.setter
    def maximum(self, value: str):
        """This function sets the maximum for this field.

        Args:
            value (str): the maximum for this field
        """   
        self._maximum = value

    
    @property
    def default(self) -> str:
        """This function returns the default for this field.

        Returns:
            str: the default for this field
        """        
        return self._default
    
    @default.setter
    def default(self, value: str):
        """This function raises a value error when trying to 
            set the default for this field, since the default
            should not be changed.

        Args:
            value (str): the default for this field
        """
        raise ValueError('Cannot set default for field: ' + self._label + \
                         '. Default should not be changed.')
    

    @property
    def var_name(self) -> str:
        """This function returns the var_name for this field.

        Returns:
            str: the var_name for this field
        """        
        return self._var_name
    

    @var_name.setter
    def var_name(self, value: str):
        """This function sets the var_name for this field.

        Args:
            value (str): the var_name for this field
        """   
        self._var_name = value

    
    @property
    def hidden(self) -> bool:
        """This function returns the hidden for this field.

        Returns:
            bool: the hidden for this field
        """        
        return self._hidden
    

    @hidden.setter
    def hidden(self, value: bool):
        """This function sets the hidden for this field.

        Args:
            value (bool): the hidden for this field
        """   
        self._hidden = value

    @property
    def count_field(self) -> str:
        """This function returns the count_field for this field.

        Returns:
            str: the count_field for this field
        """        
        return self._count_field
    

    @count_field.setter
    def count_field(self, value: str):
        """This function sets the count_field for this field.

        Args:
            value (str): the count_field for this field
        """   
        self._count_field = value


def get_widget_from_field_configs(app_configs: dict, field_configs:dict, data_filter: DataFilter, parent=None) -> QWidget:
    """This function takes a dictionary of field configurations and
    returns the appropriate widget for that field.

    Args:
        field_configs (dict): A dictionary of field configurations
            for the widget.
        app_configs (dict): A dictionary of application configurations
            for the widget.
        data_filter (DataFilter): The data filter object for this
            instance of the app.

    Returns:
        QWidget: A widget for the field, based on the field configs.
    """    
    field_configs = FieldConfigs(field_configs)
    if field_configs.hidden:
        return QWidget()
    entry_type = field_configs.type

    update_func = None
    if not pandas.isnull(field_configs.data_field):
        update_func = lambda x: data_filter.set_filter(field_configs.data_field, x)
        default = data_filter.get_filter_value(field_configs.data_field)
        if default is None:
            default = field_configs.default
            data_filter.set_filter(field_configs.data_field, default)
    else:
        if not pandas.isnull(field_configs.var_name):
            update_func = lambda x: data_filter.set_filter(field_configs.var_name, x)
            try:
                default = data_filter.get_filter_value(field_configs.var_name)
            except:
                default = None
                print ("Error getting default for var_name: " + field_configs.var_name)
        else:
            update_func = lambda x: data_filter.set_filter(field_configs.label, x)
            try:
                default = data_filter.get_filter_value(field_configs.label)
            except:
                default = None
                print ("Error getting default for label: " + field_configs.label)
        

    if entry_type == 'single-select' or entry_type == 'multi-select':
        
        dropdown_choices = []
        dropdown_values = []
        visible = True
        if not pandas.isnull(field_configs.data_field):
            visible = False
        ret_widget = StyledComboBox(
            app_configs=app_configs,
            label_text=field_configs.label,
            dropdown_choices=dropdown_choices,
            dropdown_values=dropdown_values,
            validation_function=None,
            tooltip_text=field_configs.tooltip,
            multiple_selection=True if entry_type == 'multi-select' else False,
            update_func_=update_func,
            visible=visible,
            )
        if not pandas.isnull(field_configs.data_field):
            combobox_populate_worker = PicklistPopulateWorker(
            combo_box=ret_widget,
            data_filter=data_filter,
            field_configs=field_configs,
            )
            ret_widget.set_runnable(combobox_populate_worker)
            app_configs.app_threadpool.start(combobox_populate_worker)
        return ret_widget


    elif entry_type == 'numeric':
        if field_configs.validation == 'integer':
            ret_widget = StyledIntegerSelector(
                configs=app_configs,
                label_text=field_configs.label,
                min_value=field_configs.minimum,
                max_value=field_configs.maximum,
                update_func=update_func,
                tooltip_text=field_configs.tooltip,
                parent=parent,
                default_value=default
                )
        
            return ret_widget
        
    else:
        return QWidget()