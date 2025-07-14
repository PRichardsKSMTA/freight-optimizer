from PySide6.QtWidgets import QWidget
import pandas

from .styled_hbox_layout import StyledHBoxLayout
from .styled_label import StyledLabel
from .styled_completer_combobox import StyledCompleterComboBox
from .info_tooltip import InfoTooltip
from .styled_completer_combobox_multi import StyledCompleterComboBoxMulti


class StyledComboBox(QWidget):
    """The widget is used to create a label and dropdown selector for choosing the customer
    """
    def __init__(self,
                 app_configs: dict,
                 label_text: str,
                 dropdown_choices: list,
                 dropdown_values: list=None,
                 validation_function: callable=None,
                 tooltip_text: str=None,
                 multiple_selection: bool=False,
                 update_func_: callable=None,
                 initial_selection: str=None,
                 visible: bool=True):
        """_summary_

        Args:
            app_configs (dict): dictiontary with the configurations for this applicat
            label_text (str): the text label for this widget
            dropdown_choices (list): a list of dropdown choices
            dropdown_values (list, optional): a list of values for the dropdown choices. Defaults to None.
            validation_function (callable): a function to call to validate the selection
                when the selection changes
            tooltip_text (str): the text to display when the user hovers over the widget.
                Set to None to disable the tooltip.
            update_func_ (callable): a function to call when the selection changes
        """        
        super(StyledComboBox, self).__init__()
        self.tooltip_text = tooltip_text
        self.app_configs = app_configs
        self.label_text = label_text
        self.multiple_selection = multiple_selection
        self.dropdown_choices = dropdown_choices
        if dropdown_values is None:
            dropdown_values = dropdown_choices
        self.dropdown_values = {dropdown_choices[i]: dropdown_values[i] for i in range(len(dropdown_choices))}
        self.validation_function = validation_function

        self.layout = StyledHBoxLayout(margins=(1,1,1,1))
        self.setLayout(self.layout)

        self.label = StyledLabel(label_text, app_configs=self.app_configs)
        self.layout.addWidget(self.label)

        if not multiple_selection:
            self.customer_selector = StyledCompleterComboBox(items=dropdown_choices, initial_selection=initial_selection, update_func_=update_func_)
        else:
            self.customer_selector = StyledCompleterComboBoxMulti(update_func_=update_func_)
            self.customer_selector.addItems(dropdown_choices, initial_selection=initial_selection)
        self.layout.addWidget(self.customer_selector)

        if not visible:
            self.customer_selector.hide()
            self.loading_label = StyledLabel('Loading...', app_configs=self.app_configs)
            self.layout.addWidget(self.loading_label)
            self.no_choices_label = StyledLabel('No choices available', app_configs=self.app_configs)
            self.layout.addWidget(self.no_choices_label)
            self.no_choices_label.hide()


        if tooltip_text is not None:
            self.tooltip = InfoTooltip(configs=self.app_configs, tooltip_text=tooltip_text)
            self.layout.addWidget(self.tooltip)



    def set_dropdown_choices(self, dropdown_choices: list, dropdown_values: list=None, initial_selection: list=None,
                             count_values=None):
        """ Sets the dropdown choices for this widget

        Args:
            dropdown_choices (list): a list of dropdown choices
            dropdown_values (list, optional): a list of values for the dropdown choices. Defaults to None.
        """
        try:
            self.loading_label.hide()
        except:
            pass
        if len(dropdown_choices) == 0:
            self.no_choices_label.show()
            return
        else:
            try:
                self.no_choices_label.hide()
            except:
                pass
        for i in range(self.customer_selector.count()):
            self.customer_selector.removeItem(0)
        self.dropdown_choices = dropdown_choices
        if dropdown_values is None:
            dropdown_values = dropdown_choices
        self.dropdown_values = {dropdown_choices[i]: dropdown_values[i] for i in range(len(dropdown_choices))}

        if not count_values is None:
            dropdown_choices = count_values
        # initial_selection = self.data_filter.get_selection(self.field_configs.data_field)
        if self.multiple_selection:
            self.customer_selector.addItems(dropdown_choices, initial_selection=initial_selection, datalist=dropdown_values)
            self.customer_selector.updateText()
        else:
            self.customer_selector.values.extend(dropdown_values)
            self.customer_selector.addItems(dropdown_choices)
            if not pandas.isnull(initial_selection) and len(initial_selection) > 0:
                self.customer_selector.setTextIfCompleterIsClicked(dropdown_choices[initial_selection[0]])
            else:
                self.customer_selector.setTextIfCompleterIsClicked(dropdown_choices[0])
        
        self.visible = True
        self.customer_selector.show()




    def get_selection(self) -> str:
        """Returns the selected customer

        Returns:
            str: the selected customer
        """
        selected_choice = self.customer_selector.currentText()
        try:
            return self.dropdown_values[selected_choice]
        except KeyError:
            return None
        

    def set_runnable(self, runnable) -> None:
        """Sets the widget to runnable, so that the runnable doesn't
        get cleaned up by the garbage collector.
        """
        self._runnable = runnable

    
    def set_valid(self, valid: bool, validation_message: str=None) -> None:
        """Sets the widget to valid or invalid, and sets the validation message

        Args:
            valid (bool): True if the widget is valid, False otherwise
            validation_message (str): the validation message to display
        """
        pass
        # self.tooltip.set_valid(valid)
        # if valid:
        #     self.tooltip.set_tooltip_text(self.tooltip_text)
        # else:
        #     self.tooltip.set_tooltip_text(validation_message)