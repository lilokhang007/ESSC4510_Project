import pandas as pd
import requests
import json
pd.set_option('display.max_rows', 500)

def get_raw_data_from_fetch_request(yyyy='2021'):
    # Send a request to get a xml file from HKO backend server
    page = requests.get("https://www.hko.gov.hk/cis/dailyExtract/dailyExtract_{}.xml".format(yyyy), {
      "headers": {
        "accept": "text/plain, */*; q=0.01",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": "\"Google Chrome\";v=\"89\", \"Chromium\";v=\"89\", \";Not\\\"A\\\\Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest"
      },
      "referrerPolicy": "no-referrer-when-downgrade",
      "body": None,
      "method": "GET",
      "mode": "cors",
      "credentials": "include"
    })

    # put the data in form of json
    return json.loads(page.text)['stn']['data']

if __name__ == "__main__":
    df_year = pd.DataFrame()
    for year in range(1980, 2022):
        jsonData = get_raw_data_from_fetch_request(
            yyyy = str(year)
        )

        # use year as key
        df = pd.DataFrame()
        for monthData in jsonData:
            df = pd.concat([df, pd.DataFrame(monthData).iloc[:-2]])

        df = df.reset_index()

        df[['day', 'slp', 'maxtemp', 'avgtemp', 'mintemp', 'dewtemp', 'rh', 'cld', 'rf', 'sunhr', 'prewd', 'avgws']] = pd.DataFrame(df.dayData.tolist())
        df = df.drop(['dayData', 'index'], axis=1)

        df['year'] = year
        df_year = pd.concat([df_year, df])

    df_year.drop(df_year.iloc[[14793, 14764, 14825]], axis=1)  # drop "Mean/Total"
    df_year['rf'] = df_year['rf'].replace('Trace', '  0.0')  # replace "Trace" (str) to 0 (int)
    df_year['rf'] = df_year['rf'].str.lstrip().astype(float)  # remove trailing white space

    with open("hko_data.csv".format(), 'w') as csvfile:
        df_year.to_csv(csvfile, index=False, line_terminator='\n')

