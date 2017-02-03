import React, {Component} from 'react';

class TextArea extends Component {
    render() {
        return (
            <textarea value={this.props.value} onChange={this.props.onChange}
                      name={this.props.elementConfig.id} 
                      id={this.props.elementConfig.id}
                      cols={this.props.elementConfig.cols || 30}
                      rows={this.props.elementConfig.rows || 10} ></textarea>
        );
    }
}

TextArea.propTypes = {
    value: React.PropTypes.string.isRequired,
    onChange: React.PropTypes.func.isRequired,
    elementConfig: React.PropTypes.shape({
        id: React.PropTypes.string.isRequired,
        cols:React.PropTypes.number,
        rows:React.PropTypes.number
    }).isRequired
};

export default TextArea;
