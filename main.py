import re
import string
import requests
import itertools
import threading
from os import system
from time import sleep
from random import choice

counter_list = {}
taken_names = []
available_names = []
reserved_names = []
taken_count = [0, 0]
available_count = [0, 0]
reserved_count = [0, 0]
check_fails = 0


def file2list(file: str, split_words=True):
    with open(file, 'r') as f:
        f = f.read()

    if split_words:
        return set(' '.join([line for line in f.split('\n')]).lower().split())
    else:
        return [line for line in f.split('\n')]


def wait_for_threads():
    while len(threading.enumerate()) > 1:
        print(f'Waiting on {str(len(threading.enumerate()) - 1)} threads...')
        sleep(.75)


def save_findings():
    global available_names
    global taken_names
    global reserved_names

    for name_list, file in [(available_names, 'available.txt'),
                            (taken_names, 'taken.txt'),
                            (reserved_names, 'reserved.txt')]:

        if len(name_list) > 0:
            with open(file, 'a') as f:
                f.write('\n' + '\n'.join(name_list))

    available_names = []
    taken_names = []
    reserved_names = []


def counter_list_builder(min_length: int = 4, max_length: int = 25, check_skip_list=False, no_numbers=False):

    for word in words_list:
        if not min_length <= len(word) <= max_length:
            continue
        if check_skip_list:
            if word in skip_list:
                continue
        if no_numbers:
            if not all(char in string.ascii_lowercase for char in word):  # string.ascii_lowercase + '_'
                continue
        if 'o' in word:
            o_word = re.sub('o', '0', word)
            counter_list[o_word] = 0

        counter_list[word] = 0


def twitch_check(word: [str, int]):

    if counter_list[word] < 5:
        short_url = 'twitch.tv/' + word
        long_url = 'https://www.' + short_url

        try:
            r = requests.get(long_url, timeout=3.05)
        except TimeoutError:
            return None
        except:
            print('twitch_check broke!')
            return None

        if short_url in r.text or long_url in r.text:
            taken_count[0] += 1
            del counter_list[word]
            if word not in taken_list:
                taken_count[1] += 1
                taken_names.append(word)

        else:
            try:
                counter_list[word] += 1
            except KeyError:
                print('KeyError')

    else:
        reserved_count[0] += 1
        del counter_list[word]
        if word not in reserved_list:
            reserved_count[1] += 1
            reserved_names.append(word)


def passport_check(word: [str, int]):
    # global available_count
    global check_fails
    passport = 'https://passport.twitch.tv/usernames/' + word

    try:
        r = requests.get(passport, headers={'User-Agent': choice(user_agents)}, timeout=3.05)
    except:
        print('Passport broke!')
        return None

    # print(r.status_code)
    # Name is not available, check if reserved or in use.
    if r.status_code == 200:
        twitch_check(word)

    # Name is available
    elif r.status_code == 204:
        available_count[0] += 1
        del counter_list[word]
        if word not in available_list:
            available_count[1] += 1
            available_names.append(word)

    # Too many requests
    elif r.status_code == 403:
        check_fails += 1

        # Use downtime from TIMEOUT to initiate preconnect.
        # Don't call twitch_check because it'll think the name's reserved.
        if counter_list[word] == 0:
            requests.get('https://www.twitch.tv/' + word)

    else:
        print('Passport said something weird!')
        # print(r.status_code)
        # print(r.text)


'********************************************************************'

available_list = file2list('available.txt')
reserved_list = file2list('reserved.txt')
taken_list = file2list('taken.txt')
skip_list = available_list | reserved_list | taken_list
user_agents = file2list('user agents.txt', split_words=False)

words_list = file2list('5 letter words.txt')  # This is the read-in file
counter_list_builder(min_length=4, max_length=25, check_skip_list=True, no_numbers=False)

if __name__ == '__main__':

    while len(counter_list) > 0:
        for word in dict(itertools.islice(counter_list.items(), 50)):
            # Skip passport_check if word has already been to twitch_check
            if counter_list[word] == 0:
                t = threading.Thread(target=passport_check, args=[word])
                t.start()
            else:
                t = threading.Thread(target=twitch_check, args=[word])
                t.start()

        # Make sure threads close before messing with files.
        wait_for_threads()
        # Write lists to files
        save_findings()

        # Print status
        system('cls')
        print(f'______________________\n'
              f'{len(counter_list)} left\n'
              f'{check_fails} check fails\n\n'
              f'({taken_count[1]}) {taken_count[0]} taken\n'
              f'({available_count[1]}) {available_count[0]} available\n'
              f'({reserved_count[1]}) {reserved_count[0]} reserved\n')
