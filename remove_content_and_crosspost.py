import re
def remove_contentText(text):
    #Assume contents string is text
    beg_ind = text.find("Contents\n")
    #Find last header starting point
    search_string = "\n - "
    headers = [m.end() for m in re.finditer(search_string, text[:1000])]
    last_header = headers[-1]
    header = text[last_header:last_header + 20]
    #Grab last new line index after last header + 3 (to get past original \n)
    end_ind = text[last_header:].find("\n")
    #remove content_text
    return text[:beg_ind] + text[end_ind+last_header:]


content_examples = [''''Link post\nContents\n - I. The search for discontinuities\n - II. The discontinuities\n - Large robust discontinuities\n - The Pyramid of Djoser, 2650BC\n - The SS Great Eastern\n - The first transatlantic telegraph\n - The second transatlantic telegraph\n - The first non-stop transatlantic flight\n - The George Washington Bridge\n - Nuclear weapons\n - The Paris Gun\n - The first intercontinental ballistic missiles (ICBMs)\n - YBa2Cu3O7 as a superconductor\n - Moderate robust discontinuities (10-100 years of extra progress):\n - Other places we looked\n - III. Some observations\n - Prevalence of discontinuities\n - Discontinuities go with changes in the growth rate\n - Where do we see discontinuities?\n - More things to observe\n - IV. Summary\n - Notes\nI. The search for discontinuities\n\nWe’ve been looking for historic''']

for c_ex in content_examples:
    print(remove_contentText(c_ex))