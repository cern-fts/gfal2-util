import base
import time
from base import CommandBase


class CommandLegacy(CommandBase):
    """
    Implement some legacy support around gfal2
    """

    @base.arg('lfc', action='store', type=str, help="LFC entry (lfc:// or guid:)")
    @base.arg('surl', action='store', type=str, help="Site URL to be unregistered")
    def execute_unregister(self):
        """
        Unregister a replica.
        """
        value = '-' + self.params.surl
        self.context.setxattr(self.params.lfc, 'user.replicas', value, len(value))

    @base.arg('lfc', action='store', type=str, help="LFC entry (lfc:// or guid:)")
    @base.arg('surl', action='store', type=str, help="Site URL to be unregistered")
    def execute_register(self):
        """
        Register a replica.
        """
        value = '+' + self.params.surl
        self.context.setxattr(self.params.lfc, 'user.replicas', value, len(value))

    @base.arg('lfc', action='store', type=str, help="LFC entry (lfc:// or guid:)")
    def execute_replicas(self):
        """
        List replicas.
        """
        replicas = self.context.getxattr(self.params.lfc, 'user.replicas').split('\n')
        for replica in replicas:
            print replica

    @base.arg('--pin-lifetime', action='store', type=int, default=0, help='Desired pin lifetime')
    @base.arg('--desired-request-time', action='store', type=int, default=28800, help='Desired total request time')
    @base.arg('surl', action='store', type=str, help='Site URL')
    def execute_bringonline(self):
        """
        Execute bring online
        """
        (ret, token) = self.context.bring_online(
            self.params.surl, self.params.pin_lifetime, self.params.desired_request_time, True
        )
        print "Got token", token
        wait = self.params.timeout
        sleep=1
        while ret == 0 and wait > 0:
            print "Request queued, sleep %d seconds..." % sleep
            time.sleep(sleep)
            ret = self.context.bring_online_poll(self.params.surl, token)
            wait -= 1
            sleep *= 2
            sleep = min(sleep, 300)

        if ret > 0:
            print "File brought online with token", token
        elif wait <= 0:
            raise Exception("Timeout expired while polling")
