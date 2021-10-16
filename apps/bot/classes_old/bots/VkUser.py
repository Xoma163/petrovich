from vk_api import vk_api, VkUpload

from petrovich.settings import env, BASE_DIR


class VkUser:
    def __init__(self):
        super().__init__()
        self.id = env.int('VK_USER_ID')
        vk_session = vk_api.VkApi(env.str('VK_USER_LOGIN'),
                                  env.str('VK_USER_PASSWORD'),
                                  auth_handler=self.auth_handler,
                                  config_filename=f"{BASE_DIR}/secrets/vk_user_config.json"
                                  )
        vk_session.auth()
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()

    @staticmethod
    def auth_handler():
        key = input("Enter authentication code: ")
        remember_device = True
        return key, remember_device
