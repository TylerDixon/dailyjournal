import React, {Component} from 'react';

class Choices extends Component {
    constructor(props){
        super(props);
        // Clone array
        this.state = {
            currentValue: this.props.value ? this.props.value.slice(0) : []
        }
        this.isSingleSelect = this.props.elementConfig.type === 'radio'
    }
    toggleCheckbox(event) {
        const currentValue = this.props.value;
        const currentIndex = currentValue.indexOf(event.target.value);
        if(currentIndex > -1){
            this.props.onChange({
                target: {
                    id: event.target.name,
                    value: currentValue.slice(0).splice(currentIndex, 1)
                }
            });
        }
        else {
            this.props.onChange({
                target: {
                    id: event.target.name,
                    value: currentValue.concat([event.target.value])
                }
            });
        }
    }
    isCheckboxChecked(choice) {
        return this.props.value.indexOf(choice) > -1
    }
    toggleRadio(event) {
        this.props.onChange({
            target: {
                id: event.target.name,
                value: event.target.value
            }
        });
    }
    isRadioChecked(choice) {
        return this.props.value === choice;
    }


    render() {
        var renderedChoices = this.props.elementConfig.choices.map(choice => {
            return <span><input value={choice} onChange={this.isSingleSelect ? this.toggleRadio.bind(this) : this.toggleCheckbox.bind(this)}
                          key={this.props.elementConfig.id + choice}
                   name={this.props.elementConfig.id}
                   id={this.props.elementConfig.id}
                   checked={this.isSingleSelect ? this.isRadioChecked(choice) : this.isCheckboxChecked(choice)}
                   type={this.props.elementConfig.type} />{choice}</span>
        });
        return <span>{renderedChoices}</span>;
    }
}

Choices.propTypes = {
    // value: React.PropTypes.isRequired,
    onChange: React.PropTypes.func.isRequired,
    elementConfig: React.PropTypes.shape({
        id: React.PropTypes.string.isRequired,
        choices: React.PropTypes.array.isRequired,
        type: React.PropTypes.oneOf(['checkbox', 'radio'])
    }).isRequired
};

export default Choices;
