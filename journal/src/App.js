import React, {Component} from 'react';
import './styles/css/app.css';
import request from 'es6-request';
import JournalForm from './components/JournalForm';
const API_GATEWAY_URL = 'placeholderfornow!';

class App extends Component {
    submit(data) {
        request.post(API_GATEWAY_URL)
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
