from .. import models
from .. import tasks
from .. import translator
import celery
import os


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_id):
        backend = celery.current_app.factory.create_backend()
        session = backend.session

        workflow = session.query(models.Workflow).get(workflow_id)

        petri_data = translator.build_petri_net(workflow)
        self._submit_net(petri_data, workflow.net_key)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    def _submit_net(self, petri_data, net_key):
        self.http.delay('PUT', self._petri_submit_url(net_key), **petri_data)

    def _petri_submit_url(self, net_key):
        return 'http://%s:%d/v1/nets/%s' % (
            os.environ.get('PTERO_PETRI_HOST', 'localhost'),
            int(os.environ.get('PTERO_PETRI_PORT', 80)),
            net_key,
        )
