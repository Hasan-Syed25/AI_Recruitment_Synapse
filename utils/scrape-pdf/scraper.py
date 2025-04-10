import subprocess

list_of_urls = [
    "https://app.synapserecruiternetwork.com/job-page/1742855552309x879779850003677200",
    "https://app.synapserecruiternetwork.com/job-page/1742447634868x185661387415748600",
    "https://app.synapserecruiternetwork.com/job-page/1742408181643x243451860587905020",
    "https://app.synapserecruiternetwork.com/job-page/1742319201585x332948016758521860",
    "https://app.synapserecruiternetwork.com/job-page/1742269047488x718485861762596900",
    "https://app.synapserecruiternetwork.com/job-page/1742268268675x324687029811806200",
    "https://app.synapserecruiternetwork.com/job-page/1742206296463x365381225334177800",
    "https://app.synapserecruiternetwork.com/job-page/1742205339715x304392100527472640",
    "https://app.synapserecruiternetwork.com/job-page/1742203783976x795435577009504300",
    "https://app.synapserecruiternetwork.com/job-page/1742203065358x940631092238221300",
    "https://app.synapserecruiternetwork.com/job-page/1742202212616x639695388552462300",
    "https://app.synapserecruiternetwork.com/job-page/1742200224508x128010688266240000",
    "https://app.synapserecruiternetwork.com/job-page/1742197426128x315260185657999360",
    "https://app.synapserecruiternetwork.com/job-page/1741911922476x133222905282822140",
    "https://app.synapserecruiternetwork.com/job-page/1741676447520x598560974497644500",
    "https://app.synapserecruiternetwork.com/job-page/1742200224508x128010688266240000",
    "https://app.synapserecruiternetwork.com/job-page/1742197426128x315260185657999360",
    "https://app.synapserecruiternetwork.com/job-page/1741911922476x133222905282822140",
    "https://app.synapserecruiternetwork.com/job-page/1741676447520x598560974497644500",
    "https://app.synapserecruiternetwork.com/job-page/1741675661018x673341420981190700",
    "https://app.synapserecruiternetwork.com/job-page/1741630642927x524487386063700000",
    "https://app.synapserecruiternetwork.com/job-page/1740771263559x177489019336917000",
    "https://app.synapserecruiternetwork.com/job-page/1739899618686x884476720382738400",
    "https://app.synapserecruiternetwork.com/job-page/1739466435857x758350681963233300",
    "https://app.synapserecruiternetwork.com/job-page/1739325412738x464955390864130050",
    "https://app.synapserecruiternetwork.com/job-page/1738216984152x100049871373336580",
    "https://app.synapserecruiternetwork.com/job-page/1737497600597x147290710436478980",
    "https://app.synapserecruiternetwork.com/job-page/1734655085701x861538457120145400",
    "https://app.synapserecruiternetwork.com/job-page/1730851181826x349776669277945860",
    "https://app.synapserecruiternetwork.com/job-page/1730714242415x911977541912756200",
    "https://app.synapserecruiternetwork.com/job-page/1730714078364x515091621311152100",
]

urls_done = []
for url in list_of_urls:
    if url in urls_done:
        continue
    result = subprocess.run(["pnpm", "run", "scrape", url], capture_output=True)
    if result.returncode == 0:
        print(f"Successfully scraped {url}")
        urls_done.append(url)
    else:
        print(f"Error scraping {url}: {result.stderr.decode('utf-8')}")