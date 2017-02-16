# Daily Journal
![Scrubs Unicorn](/resources/horse_with_a_sword.jpg?raw=true)
> Kelso: Write that down in your little unicorn book.

> JD: Uh, actually sir, it's a horse with a sword on his head.

### Purpose
Writing thoughts and and goals on a regular basis is healthy for the brain! This helps you do that.

### Running
* Create a virtual environment at `venv`
* `pip install -r requirements.txt`
* Create a configuration file (described below)
* `python dailyjournal.py --config=path/to/config.json`

### Configuration
Here is the full set of configuration options:
```
{
  "deployment_name": "daily-journal-deployment", // Required. Name of the created stack
  "lambda_function_prefix": "daily_journal_", // Required. Prefix to be used for all lambda function names
  "entries_bucket_name": "my-daily-journal", // Required. Name of bucket
  "api_gateway_identifier": "dj_2017", Required. Name for the deployed Gateway API
  "notification_email": "kelso@sacredheart.org", // Optional. Email for daily links to the views to create an entry for the day
  "views_authentication": "myip", // Optional. Security method for the S3 stored website. If ommitted, no policy doc will be created for the bucket. Options:
                                  // myip: Will create a policy using the API retrieved from the response of http://checkip.amazonaws.com
                                  // public: Will create a policy that allows for anyone to view the views.
  "reminder_time": "cron(0 2 * * ? *)" // Optional. The cron expression for when to send email reminders. See the cron expressiosn docs: http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html#CronExpressions for details on how to generate
}
```
