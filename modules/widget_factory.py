"""
WidgetFactory Module | by ANXETY
"""

from IPython.display import display, HTML
import ipywidgets as widgets
import time

class WidgetFactory:
    # INIT
    def __init__(self):
        self.default_style = {'description_width': 'initial'}
        self.default_layout = widgets.Layout()

    def add_classes(self, widget, class_names):
        """Add CSS classes to a widget."""
        for cls in class_names:
            widget.add_class(cls)

    # HTML
    def load_css(self, css_path):
        """Load CSS from a file and display it in the notebook."""
        try:
            with open(css_path, "r") as file:
                data = file.read()
                display(HTML(f"<style>{data}</style>"))
        except Exception as e:
            print(f"Error loading CSS: {e}")

    def load_js(self, js_path):
        """Load JavaScript from a file and display it in the notebook."""
        try:
            with open(js_path, "r") as file:
                data = file.read()
                display(HTML(f"<script>{data}</script>"))
        except Exception as e:
            print(f"Error loading JavaScript: {e}")

    def create_html(self, content, class_names=None):
        """Create an HTML widget with optional CSS classes."""
        html_widget = widgets.HTML(content)
        if class_names:
            self.add_classes(html_widget, class_names)
        return html_widget

    def create_header(self, name, class_names=None):
        """Create a header HTML widget."""
        class_names_str = ' '.join(class_names) if class_names else "header"
        header = f'<div class="{class_names_str}">{name}</div>'
        return self.create_html(header)

    # Widgets
    def _create_widget(self, widget_type, class_names=None, **kwargs):
        """Create a widget of a specified type with optional classes and styles."""
        style = kwargs.get('style', self.default_style)

        # Set default layout if not provided
        if widget_type in [widgets.Dropdown, widgets.Text]:
            if 'layout' not in kwargs and kwargs.get('reset') != True:    # reset -> return default width
                kwargs['layout'] = widgets.Layout(width='100%')

        widget = widget_type(style=style, **kwargs)

        if class_names:
            self.add_classes(widget, class_names)

        return widget

    def _apply_layouts(self, children, layouts):
        """Apply layouts to children widgets."""
        n_layouts = len(layouts)

        if n_layouts == 1:
            # Apply the single layout to all children
            for child in children:
                child.layout = layouts[0]
        else:
            for child, layout in zip(children, layouts):
                child.layout = layout

    def create_text(self, description, value='', placeholder='', class_names=None, **kwargs):
        """Create a text input widget."""
        return self._create_widget(
            widgets.Text,
            description=description,
            value=value,
            placeholder=placeholder,
            class_names=class_names,
            **kwargs
        )

    def create_dropdown(self, options, description, value, placeholder='', class_names=None, **kwargs):
        """Create a dropdown widget."""
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
        """Create a multiple select widget."""
        return self._create_widget(
            widgets.SelectMultiple,
            options=options,
            description=description,
            value=value,
            class_names=class_names,
            **kwargs
        )

    def create_checkbox(self, description, value, class_names=None, **kwargs):
        """Create a checkbox widget."""
        return self._create_widget(
            widgets.Checkbox,
            description=description,
            value=value,
            class_names=class_names,
            **kwargs
        )

    def create_button(self, description, class_names=None, **kwargs):
        """Create a button widget."""
        return self._create_widget(
            widgets.Button,
            description=description,
            class_names=class_names,
            **kwargs
        )

    def _create_box(self, box_type, children, class_names=None, **kwargs):
        """Create a box layout (horizontal or vertical) for widgets."""
        if 'layouts' in kwargs:
            self._apply_layouts(children, kwargs.pop('layouts'))

        return self._create_widget(
            box_type,
            children=children,
            class_names=class_names,
            **kwargs
        )

    def create_hbox(self, children, class_names=None, **kwargs):
        """Create a horizontal box layout for widgets."""
        return self._create_box(widgets.HBox, children, class_names, **kwargs)

    def create_vbox(self, children, class_names=None, **kwargs):
        """Create a vertical box layout for widgets."""
        return self._create_box(widgets.VBox, children, class_names, **kwargs)

    # Other
    def display(self, widgets):
        """Display one or multiple widgets."""
        if isinstance(widgets, list):
            for widget in widgets:
                display(widget)
        else:
            display(widgets)

    def close(self, widgets, class_names=None, delay=0.2):
        """Close one or multiple widgets after a delay."""
        if not isinstance(widgets, list):
            widgets = [widgets]

        if class_names:
            for widget in widgets:
                self.add_classes(widget, class_names)

        time.sleep(delay)  # closing delay for all widgets

        # Close all widgets
        for widget in widgets:
            widget.close()

    # CallBack
    def connect_widgets(self, widget_pairs, callbacks):
        """
        Connects widgets to multiple callback functions for specified property changes.

        Parameters:
        - widget_pairs: List of tuples where each tuple contains a widget and the property name to observe.
        - callbacks: List of callback functions to be called on property change.
        """
        for widget, property_name in widget_pairs:
            for callback in callbacks:
                widget.observe(lambda change, widget=widget, callback=callback: callback(change, widget), names=property_name)
