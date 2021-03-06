import React, {Component} from 'react';

class TextArea extends Component {
    render() {
        return (
            <input value={this.props.value} onChange={this.props.onChange}
                      name={this.props.elementConfig.id} 
                      id={this.props.elementConfig.id}
                      min={this.props.elementConfig.min || 0}
                      max={this.props.elementConfig.max || 100}
                      type="range"></input>
        );
    }
}


Range.propTypes = {
    value: React.PropTypes.number.isRequired,
    onChange: React.PropTypes.func.isRequired,
    elementConfig: React.PropTypes.shape({
        id: React.PropTypes.string.isRequired,
        min: React.PropTypes.number,
        max: React.PropTypes.number
    }).isRequired
};

export default TextArea;
