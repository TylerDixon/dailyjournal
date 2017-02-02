import React, {Component} from 'react';

class TextArea extends Component {
    render() {
        return (
            <textarea value={this.props.value} onChange={this.props.onChange}
                      name={this.props.elementConfig.id} 
                      id={this.props.elementConfig.id}
                      cols={this.props.elementConfig.cols || '30'}
                      rows={this.props.elementConfig.rows || '10'} ></textarea>
        );
    }
}

export default TextArea;
