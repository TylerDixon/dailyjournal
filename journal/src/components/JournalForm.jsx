import React, {Component} from 'react';
import config from '../../config.json'
import TextArea from './TextArea';
import Text from './Text';
import Number from './Number';
import Range from './Range';
import Choices from './Choices';


class JournalForm extends Component {
    constructor(props) {
        super(props);
        if (!config.formElements || !Array.isArray(config.formElements)) {
            throw new Error('Improper configuration! Configuration must have array of form elements as "formElements".')
        }

        // Set up default form values
        var defaultFormVaulues = {};
        config.formElements.forEach((formElement) => {
            defaultFormVaulues[formElement.id] = formElement.default;
        });
        this.state = {
            formValues: defaultFormVaulues
        };

    }

    handleElementChange(event) {
        this.setState(Object.assign({}, this.state, {
            formValues: Object.assign(this.state.formValues,{
                [event.target.id]: event.target.value
            })
        }));
    }
    submit(event) {
        this.props.onSubmit(this.state.formValues);

        // Prevent page reload
        event.preventDefault();
    }

    render() {
        // Render each form value according to it's configuration
        var formElementsToRender = config.formElements.map((formElement) => {
            var elementToAdd;
            switch (formElement.type) {
                case 'textarea':
                    elementToAdd = <TextArea value={this.state.formValues[formElement.id]}
                                             onChange={this.handleElementChange.bind(this)}
                                             elementConfig={formElement}></TextArea>;
                    break;
                case 'text':
                    elementToAdd = <Text value={this.state.formValues[formElement.id]}
                                         onChange={this.handleElementChange.bind(this)}
                                         elementConfig={formElement}></Text>;
                    break;
                case 'number':
                    elementToAdd = <Number value={this.state.formValues[formElement.id]}
                                           onChange={this.handleElementChange.bind(this)}
                                           elementConfig={formElement}></Number>;
                    break;
                case 'range':
                    elementToAdd = <Range value={this.state.formValues[formElement.id]}
                                          onChange={this.handleElementChange.bind(this)}
                                          elementConfig={formElement}></Range>;
                    break;
                case 'checkbox':
                case 'radio':
                    elementToAdd = <Choices value={this.state.formValues[formElement.id]}
                                            onChange={this.handleElementChange.bind(this)}
                                            elementConfig={formElement}></Choices>;
                    break;
            }

            return <div className="form-element-container">
                    <h2>{formElement.title}</h2>
                    {elementToAdd}
                </div>
        });
        return (
            <form onSubmit={this.submit.bind(this)}>
                {formElementsToRender}
                <input type="submit" value="Submit" />
            </form>
        );
    }
}

export default JournalForm;
