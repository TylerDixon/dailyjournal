import React, {Component} from 'react';

class Text extends Component {
    render() {
        return (
            <input value={this.props.value} onChange={this.props.onChange}
                      name={this.props.elementConfig.id}
                      id={this.props.elementConfig.id}
                      type="text" ></input>
        );
    }
}

Text.propTypes = {
    value: React.PropTypes.string.isRequired,
    onChange: React.PropTypes.func.isRequired,
    elementConfig: React.PropTypes.shape({
        id: React.PropTypes.string.isRequired
    }).isRequired
};

export default Text;
