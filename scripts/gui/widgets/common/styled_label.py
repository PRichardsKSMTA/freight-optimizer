from PySide6.QtWidgets import QLabel

class StyledLabel(QLabel):
    '''
    This is a common checkbox that will maintain the same style 
    across the application
    '''

    def __init__(self, text, app_configs, label_type='main', parent=None, text_color=None):
        super(StyledLabel, self).__init__(text, parent)
 
        if label_type not in ['main', 'header']:
            raise ValueError('label_type must be either "main" or "header"')
        font_family = app_configs.get_application_setting('font_family')
        label_settings = app_configs.get_application_setting('label', label_type)

        if text_color is not None:
            label_settings['text_color'] = text_color

        self.setStyleSheet('''
            QLabel {
                font-family: %s;
                font-size: %spx;
                font-weight: %s;
                color: %s;
                background-color: None;
                border-radius: 5px;
                padding: 5px;
                padding-top: 2px;
                padding-bottom: 2px;
                line-height: 1.2;
            }
            ''' % (
                font_family,
                label_settings['font_size'], 
                label_settings['font_weight'],
                text_color
                )
            )