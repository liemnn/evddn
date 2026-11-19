/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class EkidsTrialStepperWidget extends Component {
    static props = { ...standardFieldProps };

    static template = xml`
        <div class="ekids-kd-stepper">
            <button type="button"
                    class="ekids-kd-step-btn"
                    title="Giảm 1 lần"
                    t-att-disabled="props.readonly or currentValue &lt;= 0"
                    t-on-click="() => this.step(-1)">−</button>

            <input type="number"
                   inputmode="numeric"
                   class="ekids-kd-step-input"
                   min="0"
                   t-att-max="maxTrials"
                   t-att-readonly="props.readonly"
                   t-att-value="currentValue"
                   t-on-keydown="onKeydown"
                   t-on-input="onInput"
                   t-on-blur="onBlur"/>

            <button type="button"
                    class="ekids-kd-step-btn"
                    title="Tăng 1 lần"
                    t-att-disabled="props.readonly or currentValue &gt;= maxTrials"
                    t-on-click="() => this.step(1)">+</button>
        </div>
    `;

    get maxTrials() {
        const rawMax = this.props.record?.data?.solan_thu;
        return Number(rawMax) > 0 ? Number(rawMax) : 10;
    }

    get currentValue() {
        const val = this.props.record?.data?.[this.props.name];
        return val !== undefined && val !== false ? Number(val) : 0;
    }

    async commitValue(rawVal) {
        if (this.props.readonly) return;
        let val = parseInt(rawVal, 10);
        if (isNaN(val) || val < 0) val = 0;
        if (val > this.maxTrials) val = this.maxTrials;

        await this.props.record.update({ [this.props.name]: val });
    }

    step(delta) {
        this.commitValue(this.currentValue + delta);
    }

    onKeydown(ev) {
        if (["e", "E", "+", "-", ".", ","].includes(ev.key)) {
            ev.preventDefault();
        }
    }

    onInput(ev) {
        const digits = String(ev.target.value || "").replace(/\D+/g, "");
        if (digits === "") return;
        let val = parseInt(digits, 10);
        if (val > this.maxTrials) {
            val = this.maxTrials;
            ev.target.value = String(val);
        }
        this.commitValue(val);
    }

    onBlur(ev) {
        const val = ev.target.value === "" ? 0 : ev.target.value;
        ev.target.value = String(Math.min(Math.max(parseInt(val, 10) || 0, 0), this.maxTrials));
        this.commitValue(ev.target.value);
    }
}

registry.category("fields").add("ekids_trial_stepper", {
    component: EkidsTrialStepperWidget,
    supportedTypes: ["integer"],
});