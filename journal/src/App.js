import React, {Component} from 'react';
import './styles/css/app.css';
import request from 'request-promise';
import JournalForm from './components/JournalForm';
const API_GATEWAY_URL = process.env.REACT_APP_GATEWAY_URL || 'Gateway URL not properly set.';

class App extends Component {
    submit(data) {
        request.post({
                uri: API_GATEWAY_URL,
                json: data
            })
            .json(data)
            .then(res => {
                console.log(res);
            })
    }
    render() {
        return (
            <div className="App">
                <JournalForm onSubmit={this.submit.bind(this)}></JournalForm>
            </div>
        );
    }
}

export default App;
