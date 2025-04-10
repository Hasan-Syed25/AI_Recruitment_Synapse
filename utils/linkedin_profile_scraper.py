from proxycurl.asyncio import Proxycurl
import pandas as pd
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
proxycurl_api_key = os.getenv("PROXY_CURL_API_KEY")

# extract linkedin profile data using Proxycurl API from juicebox
file_path = '../data/candidates/JuiceboxExport_1743820890826.csv'
# read the CSV file using pandas
df = pd.read_csv(file_path, encoding='utf-8')

# read Linkedin profile URLs from the CSV file
linkedin_profile_urls = []
for index, row in df.iterrows():
	linkedin_profile_url = row['LinkedIn']
	if pd.notna(linkedin_profile_url):
		linkedin_profile_urls.append(linkedin_profile_url)

# Take only the first 10 URLs
linkedin_profile_urls = linkedin_profile_urls[:5]

# Create output directory if it doesn't exist
output_dir = '../data/candidates/'
os.makedirs(output_dir, exist_ok=True)

async def scrape_profiles():
	proxycurl = Proxycurl(api_key="")
	all_profiles = []
	
	try:
		for i, url in enumerate(linkedin_profile_urls):
			print(f"Scraping profile {i+1}/{len(linkedin_profile_urls)}: {url}")
			try:
				person = await proxycurl.linkedin.person.get(linkedin_profile_url=url)
				all_profiles.append(person)
				print(f"Profile scraped successfully")
			except Exception as e:
				print(f"Error scraping {url}: {str(e)}")
		
		output_file = os.path.join(output_dir, "first_five_profiles.json")
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(all_profiles, f, indent=2)
			
		print(f"Saved {len(all_profiles)} profiles to {output_file}")
	except Exception as e:
		print(f"An unexpected error occurred: {str(e)}")

# Run the async function
asyncio.run(scrape_profiles())