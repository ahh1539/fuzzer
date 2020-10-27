import mechanicalsoup
import time
import argparse
from urllib.parse import urlparse

browser = mechanicalsoup.StatefulBrowser(raise_on_404=True)


def dvwa_setup(path) -> None:
    # creates new database
    browser.open(path + 'setup.php')
    # print(browser.get_url())
    browser.select_form('form[action="#"]')
    browser.submit_selected()

    # logs user into dvwa
    browser.open(path + 'login.php')
    browser.select_form('form[action="login.php"]')
    browser['username'] = 'admin'
    browser['password'] = 'password'
    browser.submit_selected()
    print('LOGGED IN')

    # sets security level to low
    browser.open(path + 'security.php')
    browser.select_form('form[action="#"]')
    browser['security'] = 'low'
    browser.submit_selected()
    # browser.launch_browser()
    print('SECURITY LEVEL SET TO LOW')


def discover_common_words(path, filename, extension):
    if not path[-1] == '/':
        path += '/'
    working_links = []
    common = open(filename, 'r')
    for base_link in common:
        endings = open(extension, 'r')
        for link_ending in endings:
            try:
                browser.open(path + base_link.strip() + link_ending.strip())
                working_links.append(path + base_link.strip() + link_ending.strip())
            except:
                pass
    print('*' * 100 + '\n' + 'Links guessed using {}\n'.format(filename) + '*' * 100)
    for link in working_links:
        print(link)
    print('*' * 100)
    return working_links


# recursively finds all the links on all the pages
def recursive_discover(path, urls_to_visit, visited_urls, recursive_calls=0):
    if len(urls_to_visit) > 0 and recursive_calls <= 40:

        if urls_to_visit[0] in visited_urls:
            urls_to_visit = urls_to_visit[1:]
            return recursive_discover(path, urls_to_visit, visited_urls, recursive_calls + 1)

        browser.open(urls_to_visit[0])
        try:
            for link in browser.links():
                if 'http' not in link['href'] and 'logout' not in link['href']:
                    browser.follow_link(link)
                    if browser.get_url() in visited_urls or browser.get_url() in urls_to_visit:
                        browser.open(urls_to_visit[0])
                        continue
                    elif not link['href'].startswith('http'):
                        urls_to_visit.append(browser.get_url())
                        browser.open(urls_to_visit[0])
        except:
            pass
        if urls_to_visit:
            visited_urls.append(urls_to_visit[0])
            urls_to_visit.remove(urls_to_visit[0])
        return recursive_discover(path, urls_to_visit, visited_urls, recursive_calls + 1)
    else:
        return visited_urls


# gets all the cookies for the pages
def get_all_links_and_cookies(path, to_visit=[]):
    browser.open(path)
    print('*' * 100 + '\n' + 'Cookies\n' + '*' * 100)
    for cookie in browser.session.cookies.items():
        print(cookie)
    print('*' * 100)

    visited = []

    for found_link in browser.links()[1:]:
        if not found_link['href'].startswith('http') and 'logout' not in found_link['href']:
            try:
                browser.open(path)
                browser.follow_link(found_link)
                to_visit.append(browser.get_url())
            except:
                pass
    browser.open(path)
    try:
        browser.follow_link(browser.links()[0])
        visited.append(browser.get_url())
        browser.open(path)
    except:
        visited.append(path)
    start_time = time.time()
    recursive_discover(path, to_visit, visited)

    print('*' * 100 + '\n' + 'Links Recursively Found, Done in: {} seconds\n'.format(
        time.time() - start_time) + '*' * 100)
    for item in visited:
        print(item)
    print('*' * 100)
    return visited


# finds all the inputs on the pages
def find_forms(links, sensitive_file=None, vectors_file=None, test=False, slow=None):
    total_unsanitized = 0
    total_sensitive = 0
    for link in links:
        browser.open(link)
        if browser.get_current_page() and browser.get_current_page().find_all('input'):
            print('*' * 100 + '\nINPUTS ON PAGE: {}\n'.format(link) + '*' * 100)
            print('{0:10}  {1}'.format('NAME', 'VALUE'))
            for input_field in browser.get_current_page().find_all('input'):
                print('{0:10}  {1}'.format(input_field.get('name', 'none'), input_field.get('value', 'none')))
            if urlparse(link).query:
                print('{0:10}  {1}'.format(urlparse(link).query.split("=")[0], urlparse(link).query.split("=")[1]))
            if test:
                try:
                    for curr_form in browser.get_current_page().find_all('form'):
                        browser.select_form(curr_form)
                        vectors = open(vectors_file, 'r')
                        for vector in vectors:
                            browser.select_form(curr_form)
                            for selected_input in browser.get_current_form().form.find_all(
                                    ("input", "textarea", "select")):
                                if selected_input['type'] == 'text':
                                    browser[selected_input['name']] = vector
                            response = browser.submit_selected()
                            if not response.status_code == 200:
                                print('Error code: {} on page {}'.format(response.status_code, browser.get_url()))
                            if vector in response.text:
                                print('The following is not being sanitized: {}'.format(vector.strip()))
                                total_unsanitized += 1
                            total_sensitive += check_sensitive(response, sensitive_file)
                            check_response_time(response, slow)
                except:
                    print('NO FORM TO SUBMIT FOUND')
    if test:
        print('*' * 100 + '\n' + '*' * 100 + '\n' + 'Total Unsanitized: {}'.format(total_unsanitized))
        print('Total Sensitive: {}'.format(total_sensitive))


def check_sensitive(response, sensitive):
    sensitive_words = open(sensitive, 'r')
    for word in sensitive_words:
        if word in response.text:
            print('Sensitive word found: {}'.format(word))
            return 1
    return 0


def check_response_time(response, slow):
    load_time = response.elapsed.total_seconds() * 1000
    if load_time > slow:
        print("Response took {} ms, Potential Denial Of Service Vulnerability".format(load_time))


def check_args() -> None:
    slow = 500
    common_words_file = 'data/common_names.txt'
    extensions_file = 'data/base_extensions.txt'
    sensitive_file = 'data/sensitive.txt'
    vectors_file = 'data/vectors.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument("discover_or_test",
                        help='Keyword to specify what type to run [discover | test], always followed by url')
    parser.add_argument("discover_url", help="Specify the base url to find DVWA")

    parser.add_argument("--custom-auth", help="Specify the custom-auth, --custom-auth=dvwa")
    parser.add_argument("--common-words",
                        help="Newline-delimited file of common words to be used in page guessing. Required.")
    parser.add_argument("--extensions", help="Newline-delimited file of path extensions")
    parser.add_argument("--vectors", help="Newline-delimited file of common exploits to vulnerabilities. Required.")
    parser.add_argument("--sanitized-chars",
                        help="Newline-delimited file of characters that should be sanitized from inputs. Defaults to just < and >")
    parser.add_argument("--sensitive",
                        help="Newline-delimited file data that should never be leaked. It's assumed that this data is in the application's database (e.g. test data), but is not reported in any response. Required.")
    parser.add_argument("--slow",
                        help="Number of milliseconds considered when a response is considered 'slow'. Optional. Default is 500 miliseconds")

    args = parser.parse_args()
    parser.parse_args()
    if args.discover_or_test == 'discover' and args.discover_url:
        discover_path = args.discover_url
        if args.custom_auth == 'dvwa':
            dvwa_setup(discover_path)
        if args.common_words:
            common_words_file = args.common_words
        if args.extensions:
            extensions_file = args.extensions
        working_links = discover_common_words(discover_path, common_words_file, extensions_file)
        visited = get_all_links_and_cookies(discover_path, to_visit=working_links)
        find_forms(visited)
    elif args.discover_or_test == 'test' and args.discover_url:
        discover_path = args.discover_url
        if args.custom_auth == 'dvwa':
            dvwa_setup(discover_path)
        if args.common_words:
            common_words_file = args.common_words
        if args.extensions:
            extensions_file = args.extensions
        if args.sensitive:
            sensitive_file = args.sensitive
        if args.vectors:
            vectors_file = args.vectors
        if args.slow:
            slow = int(args.slow)
        working_links = discover_common_words(discover_path, common_words_file, extensions_file)
        visited = get_all_links_and_cookies(discover_path, to_visit=working_links)
        find_forms(visited, sensitive_file=sensitive_file, vectors_file=vectors_file, test=True, slow=slow)


if __name__ == '__main__':
    check_args()
