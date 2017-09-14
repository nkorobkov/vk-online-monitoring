import csv
import datetime
import time
import vk
import os

INTERVAL_S = 3 * 60
ONLINE_POSTFIX = "@ONLINE"
PLATFORM_POSTFIX = "@PLATFORM"
LAST_SEEN_POSTFIX = "@LAST_SEEN"
NOT_AVALIABLE = "NA"
DIR_NAME = 'data'


class OnlineGatherer:
    user_id = ''
    vkapi = None
    watch_list = None

    def conect(self):
        attempt = 0
        while -1 < attempt < 3:
            self.user_id = input('You can see more info if you log in\nPlease type your phone or leave blank to skip\n')
            password = input('Password:\n') if self.user_id else ''
            try:
                session = vk.AuthSession(app_id='5164278', user_login=self.user_id,
                                         user_password=password) if password else vk.AuthSession()
                attempt = -1
            except vk.exceptions.VkAuthError:
                attempt += 1
                print(
                    'Seems like some of your credentials are wrong. Please try again. You can leave password blank.\n')

        if attempt == 3:
            raise RuntimeError("You tried to enter password three times. Exiting.\n")
        self.vkapi = vk.API(session)

    def construct_watch_list_for_target(self, target_id):
        if not target_id:
            if not self.user_id:
                raise RuntimeError("You are not logged in and did not specified target ID. Exiting.\n")
            target_id_for_list = self.vkapi.account.getProfileInfo()['screen_name']
            target_id = self.user_id
        else:
            target_id_for_list = target_id
        self.watch_list = [target_id_for_list] + self.vkapi.friends.get(user_id=target_id, order='hints')

    def get_targets_online(self):
        return self.vkapi.users.get(user_ids=self.watch_list, fields='last_seen, online')


def main():
    gatherer = OnlineGatherer()
    gatherer.conect()
    target_id = input("Target ID (blank to track yourself if you logged in)\n")
    gatherer.construct_watch_list_for_target(target_id)
    if not os.path.exists(DIR_NAME):
        os.makedirs(DIR_NAME)
    start_time = datetime.datetime.today().ctime()
    file_name = '{}/{} started {}.csv'.format(DIR_NAME, gatherer.watch_list[0], start_time)
    users = gatherer.get_targets_online()
    header_row = ['timestamp']
    for info in users:
        name = '{} {}'.format(info['first_name'], info['last_name'])
        name += '{}'
        header_row.extend([name.format(ONLINE_POSTFIX), name.format(PLATFORM_POSTFIX), name.format(LAST_SEEN_POSTFIX)])
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header_row)

    while True:
        row = [round(datetime.datetime.now().timestamp())]
        for info in users:
            row.append(info.get('online', NOT_AVALIABLE))
            row.append(info.get('last_seen', {}).get('platform', NOT_AVALIABLE))
            row.append(info.get('last_seen', {}).get('time', NOT_AVALIABLE))
        with open('{}/{} started {}.csv'.format(DIR_NAME, gatherer.watch_list[0], start_time), 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print('Data saved for {} users at {}'.format(len(users), datetime.datetime.today().ctime()))
        time.sleep(INTERVAL_S)
        users = gatherer.get_targets_online()


if __name__ == '__main__':
    main()
