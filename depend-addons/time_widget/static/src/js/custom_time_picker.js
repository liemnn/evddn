/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
const { Component, useRef } = owl;
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Flatpickr-based Time Picker Widget
 */
export class FieldFlatpickrTime extends Component {
    static template = 'FieldFlatpickrTime';
    setup() {
        this.input = useRef('input_time');
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            refName: "input_time"
        });
    }

    _onClickTimeField(ev) {
        if (this.props.record.fields[this.props.name].type === "char") {
            if (typeof flatpickr === 'undefined') {
                console.error('Flatpickr is not loaded. Please ensure it is included in your assets.');
                return;
            }
            flatpickr(this.input.el, {
                enableTime: true,
                noCalendar: true,
                dateFormat: "H : i",
                time_24hr: true,
                defaultDate: this.input.el.value || "00:00",
                onClose: (selectedDates, dateStr) => {
                    if (dateStr) {
                        this.props.record.update({ [this.props.name]: dateStr });
                    }
                }
            }).open();
        } else {
            this.env.model.dialog.add(AlertDialog, {
                body: _t("This widget can only be added to 'Char' field"),
            });
        }
    }
}

FieldFlatpickrTime.props = {
    ...standardFieldProps,
}

export const FlatpickrTimeField = {
    component: FieldFlatpickrTime,
    supportedTypes: ["char"],
};

registry.category("fields").add("flatpickr_time", FlatpickrTimeField);
