""" Widget Factory: ipywidgets Builders & Layout Helpers | by ANXETY """

import time

import ipywidgets as widgets

from IPython.display import HTML, display


class WidgetFactory:
    # ~~ INIT ~~

    def __init__(self):
        self.default_style  = {'description_width': 'initial'}
        self.default_layout = widgets.Layout()

    def _validate_class_names(self, class_names):
        """Validate and normalize class names"""
        if class_names is None:
            return []
        if isinstance(class_names, str):
            return [class_names.strip()]
        if isinstance(class_names, list):
            return [cls.strip() for cls in class_names if cls.strip()]

        print(f"WARNING: Invalid class_names type: {type(class_names).__name__}")
        return []

    def add_classes(self, widget, class_names):
        """Add CSS classes to a widget"""
        for cls in self._validate_class_names(class_names):
            widget.add_class(cls)


    # ~~ HTML ~~

    def _load_asset(self, path, tag, name):
        """Load a CSS/JS asset and display it in the notebook"""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                display(HTML(f'<{tag}>{file.read()}</{tag}>'))
        except Exception as exc:
            print(f"Error loading {name}: {exc}")

    def load_css(self, css_path):
        self._load_asset(css_path, 'style', 'CSS')

    def load_js(self, js_path):
        self._load_asset(js_path, 'script', 'JavaScript')

    def create_html(self, content, class_names=None):
        """Create an HTML widget with optional CSS classes"""
        widget = widgets.HTML(content)
        if class_names:
            self.add_classes(widget, class_names)
        return widget

    def create_header(self, name, class_names=None):
        """Create a header HTML widget"""
        classes = ' '.join(self._validate_class_names(class_names)) or 'header'
        return self.create_html(f'<div class="{classes}">{name}</div>')


    # ~~ WIDGETS ~~

    def _apply_layouts(self, children, layouts):
        """Apply layouts to children widgets"""
        if len(layouts) == 1:
            layouts *= len(children)
        for child, layout in zip(children, layouts):
            child.layout = layout

    def _create_widget(self, widget_type, class_names=None, **kwargs):
        """Create a widget of a specified type with optional classes and styles"""
        style = kwargs.pop('style', self.default_style)

        if widget_type in [widgets.Text, widgets.Dropdown, widgets.Textarea] and 'layout' not in kwargs:
            kwargs['layout'] = widgets.Layout(width='100%')

        widget = widget_type(style=style, **kwargs)
        if class_names:
            self.add_classes(widget, class_names)

        return widget

    def _create_input(self, widget_type, description, value='', placeholder='', class_names=None, **kwargs):
        """Create an input widget of given type"""
        return self._create_widget(
            widget_type,
            description=description,
            value=value,
            placeholder=placeholder,
            class_names=class_names,
            **kwargs
        )

    def create_file_upload(self, accept, multiple=False, description='', class_names=None, **kwargs):
        """Create a FileUpload widget"""
        accept = accept if isinstance(accept, str) else ','.join(accept)
        return self._create_widget(
            widgets.FileUpload,
            accept=accept,
            multiple=multiple,
            description=description,
            class_names=class_names,
            **kwargs
        )

    def create_text(self, description, value='', placeholder='', class_names=None, **kwargs):
        return self._create_input(widgets.Text, description, value, placeholder, class_names, **kwargs)

    def create_textarea(self, description, value='', placeholder='', class_names=None, **kwargs):
        return self._create_input(widgets.Textarea, description, value, placeholder, class_names, **kwargs)

    def create_dropdown(self, options, description, value=None, placeholder='', class_names=None, **kwargs):
        """Create a dropdown with simple 'in' matching | supports (label, value) tuples"""
        def val_of(opt):
            return opt[1] if isinstance(opt, tuple) else opt

        def pick(val, opts):
            if not val:
                return val_of(opts[0])
            val_l = str(val).lower()
            for opt in opts:
                if val_l == str(val_of(opt)).lower():
                    return val_of(opt)
            for opt in opts:
                if val_l in str(val_of(opt)).lower():
                    return val_of(opt)
            return val_of(opts[0])

        if options:
            value = pick(value, options)

        return self._create_widget(
            widgets.Dropdown,
            options=options,
            description=description,
            value=value,
            placeholder=placeholder,
            class_names=class_names,
            **kwargs
        )

    def create_select_multiple(self, options, description, value=None, class_names=None, **kwargs):
        """Create a multiple select widget"""
        if isinstance(value, str):
            value = (value,)
        elif value is None:
            value = ()

        return self._create_widget(
            widgets.SelectMultiple,
            options=options,
            description=description,
            value=value,
            class_names=class_names,
            **kwargs
        )

    def create_checkbox(self, description, value=False, class_names=None, **kwargs):
        return self._create_widget(widgets.Checkbox, description=description, value=value, class_names=class_names, **kwargs)

    def create_button(self, description, class_names=None, **kwargs):
        return self._create_widget(widgets.Button, description=description, class_names=class_names, **kwargs)

    def _create_box(self, box_type, children, class_names=None, **kwargs):
        """Create a box layout (horizontal or vertical) for widgets"""
        if 'layouts' in kwargs:
            self._apply_layouts(children, kwargs.pop('layouts'))

        return self._create_widget(box_type, children=children, class_names=class_names, **kwargs)

    def create_hbox(self, children, class_names=None, **kwargs):
        """Create a horizontal box layout for widgets"""
        return self._create_box(widgets.HBox, children, class_names, **kwargs)

    def create_vbox(self, children, class_names=None, **kwargs):
        """Create a vertical box layout for widgets"""
        return self._create_box(widgets.VBox, children, class_names, **kwargs)

    def create_box(self, children, direction='column', wrap=True, class_names=None, **kwargs):
        """Create a flexible Box container with adjustable direction and wrapping"""
        if direction not in ('row', 'column'):
            raise ValueError(f"Invalid direction: {direction}. Use 'row' or 'column'.")

        layout = kwargs.pop('layout', {})
        layout.update({
            'flex_flow': direction,
            'flex_wrap': 'wrap' if wrap else 'nowrap'
        })
        return self._create_box(widgets.Box, children, class_names=class_names, layout=layout, **kwargs)


    # ~~ OTHER ~~

    def display(self, widgets):
        """Display one or multiple widgets"""
        if isinstance(widgets, list):
            for widget in widgets:
                display(widget)
        else:
            display(widgets)

    def close(self, widgets, class_names=None, delay=0.2):
        """Close one or multiple widgets after a delay"""
        if not isinstance(widgets, list):
            widgets = [widgets]
        if class_names:
            for widget in widgets:
                self.add_classes(widget, class_names)

        time.sleep(delay)
        for widget in widgets:
            widget.close()


    # ~~ CALLBACK ~~

    def connect_widgets(self, widget_pairs, callbacks):
        """Connect widgets to callbacks for specified property changes"""
        if not isinstance(callbacks, list):
            callbacks = [callbacks]

        for widget, property_name in widget_pairs:
            for callback in callbacks:
                widget.observe(lambda change, widget=widget, callback=callback: callback(change, widget), names=property_name)
