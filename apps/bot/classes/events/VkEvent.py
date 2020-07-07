from apps.bot.classes.events.Event import Event, auto_str
from petrovich.settings import VK_URL


@auto_str
class VkEvent(Event):
    def parse_attachments(self, vk_attachments):
        attachments = []

        if vk_attachments:
            for attachment in vk_attachments:
                attachment_type = attachment[attachment['type']]

                new_attachment = {
                    'type': attachment['type']
                }
                if 'owner_id' in attachment_type:
                    new_attachment['owner_id'] = attachment_type['owner_id']
                if 'id' in attachment_type:
                    new_attachment['id'] = attachment_type['id']
                if attachment['type'] in ['photo', 'video', 'audio', 'doc']:
                    new_attachment[
                        'vk_url'] = f"{attachment['type']}{attachment_type['owner_id']}_{attachment_type['id']}"
                    new_attachment['url'] = f"{VK_URL}{new_attachment['vk_url']}"
                if attachment['type'] == 'photo':
                    max_size_image = attachment_type['sizes'][0]
                    max_size_width = max_size_image['width']
                    for size in attachment_type['sizes']:
                        if size['width'] > max_size_width:
                            max_size_image = size
                            max_size_width = size['width']
                        new_attachment['download_url'] = max_size_image['url']
                        new_attachment['size'] = {
                            'width': max_size_image['width'],
                            'height': max_size_image['height']}
                elif attachment['type'] == 'video':
                    new_attachment['title'] = attachment_type['title']
                elif attachment['type'] == 'audio':
                    new_attachment['artist'] = attachment_type['artist']
                    new_attachment['title'] = attachment_type['title']
                    new_attachment['duration'] = attachment_type['duration']
                    new_attachment['download_url'] = attachment_type['url']
                elif attachment['type'] == 'doc':
                    new_attachment['title'] = attachment_type['title']
                    new_attachment['ext'] = attachment_type['ext']
                    new_attachment['download_url'] = attachment_type['url']
                elif attachment['type'] == 'wall':
                    if 'attachments' in attachment_type:
                        new_attachment['attachments'] = self.parse_attachments(attachment_type['attachments'])
                    elif 'copy_history' in attachment_type and len(
                            attachment_type['copy_history']) > 0 and 'attachments' in \
                            attachment_type['copy_history'][0]:
                        new_attachment['attachments'] = self.parse_attachments(
                            attachment_type['copy_history'][0]['attachments'])
                elif attachment['type'] == 'audio_message':
                    new_attachment['download_url'] = attachment_type['link_mp3']
                    new_attachment['duration'] = attachment_type['duration']
                elif attachment['type'] == 'link':
                    new_attachment['url'] = attachment_type['url']
                    new_attachment['title'] = attachment_type['title']
                    new_attachment['description'] = attachment_type['description']
                    new_attachment['caption'] = attachment_type['caption']

                attachments.append(new_attachment)

        if attachments and len(attachments) > 0:
            return attachments
        else:
            return None

    def __init__(self, event):
        super().__init__(event)
