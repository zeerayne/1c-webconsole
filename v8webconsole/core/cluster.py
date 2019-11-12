import logging
import pythoncom
import win32com.client

"""
Для доступа к информационной базе из внешней программы используется COM объект COMConnector. 
В зависимости от версии платформы используется V82.COMConnector или V83.COMConnector. При установке платформы 1С, 
операционной системе автоматически регистрируется класс COMConnector. 
Если по каким либо причинам регистрация не прошла, то его можно зарегистрировать вручную.

Если COMConnector не зарегистрирован в Windows, то при программном создании объекта будет появляться ошибка:
> Ошибка при вызове конструктора (COMObject): -2147221164(0x80040154): Класс не зарегистрирован.

Для того чтобы зарегистрировать ComConnector в 64 разрядной операционной системе Windows выполняется
команда: regsvr32 "C:\Program Files (x86)\1cv8\[version]\bin\comcntr.dll" 
"""
from typing import Mapping, Tuple


class ClusterControlInterface:
    """
    Примечание: любые COM-объекты не могут быть переданы между потоками,
    и должны использоваться только в потоке, в котоорм были созданы
    """

    def __init__(self, host: str, port: int, cluster_admin_name: str, cluster_admin_pwd: str,
                 infobases_credentials: Mapping[str, Tuple]):
        pythoncom.CoInitialize()
        # В зависимости от версии платформы используется V82.COMConnector или V83.COMConnector
        try:
            self.V8COMConnector = win32com.client.Dispatch("V83.COMConnector")
        except pythoncom.com_error:
            self.V8COMConnector = win32com.client.Dispatch("V82.COMConnector")
        self.host = host
        self.agent_port = str(port)
        self.cluster_admin_name = cluster_admin_name
        self.cluster_admin_pwd = cluster_admin_pwd
        self.infobases_credentials = infobases_credentials

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del self.V8COMConnector

    def get_agent_connection(self):
        agent_connection = self.V8COMConnector.ConnectAgent("{0}:{1}".format(self.host, self.agent_port))
        return agent_connection

    def get_cluster(self, agent_connection):
        """
        Получает первый кластер из списка
        :param agent_connection: Соединение с агентом сервера
        :return: Объект IClusterInfo
        """
        cluster = agent_connection.GetClusters()[0]
        return cluster

    def cluster_auth(self, agent_connection, cluster):
        """
        Авторизует соединение с агентом сервера для указанного кластера. Данные для авторизации берутся из настроек
        :param agent_connection: Соединение с агентом сервера
        :param cluster: Кластер
        """
        agent_connection.Authenticate(cluster, self.cluster_admin_name, self.cluster_admin_pwd)

    def get_cluster_with_auth(self, agent_connection):
        cluster = self.get_cluster(agent_connection)
        self.cluster_auth(agent_connection, cluster)
        return cluster

    def get_working_process_connection(self):
        agent_connection = self.get_agent_connection()
        cluster = self.get_cluster_with_auth(agent_connection)

        working_process_0 = agent_connection.GetWorkingProcesses(cluster)[0]
        working_process_port = str(working_process_0.MainPort)
        working_process_connection = self.V8COMConnector.ConnectWorkingProcess(
            'tcp://{0}:{1}'.format(self.host, working_process_port)
        )
        # Выполняет аутентификацию администратора кластера.
        # Администратор кластера должен быть аутентифицирован для создания в этом кластере новой информационной базы.
        working_process_connection.AuthenticateAdmin(self.cluster_admin_name, self.cluster_admin_pwd)
        return working_process_connection

    def get_working_process_connection_with_info_base_auth(self):
        working_process_connection = self.get_working_process_connection()
        # Административный доступ разрешен только к тем информационным базам,
        # в которых зарегистрирован пользователь с таким именем и он имеет право "Администратор".
        for c in self.infobases_credentials.values():
            working_process_connection.AddAuthentication(c[0], c[1])
        return working_process_connection

    def _get_info_base(self, info_bases, name):
        for ib in info_bases:
            if ib.Name.lower() == name.lower():
                return ib

    def get_info_bases(self, working_process_connection):
        info_bases = working_process_connection.GetInfoBases()
        return info_bases

    def get_info_base(self, working_process_connection, name):
        info_bases = self.get_info_bases(working_process_connection)
        return self._get_info_base(info_bases, name)

    def get_info_bases_short(self, agent_connection, cluster):
        info_bases_short = agent_connection.GetInfoBases(cluster)
        return info_bases_short

    def get_info_base_short(self, agent_connection, cluster, name):
        info_bases_short = self.get_info_bases_short(agent_connection, cluster)
        return self._get_info_base(info_bases_short, name)

    def get_info_base_metadata(self, info_base, info_base_user, info_base_pwd):
        """
        Получает наименование и версию конфигурации
        :param info_base: COM-Объект типа IInfoBaseShort или IInfoBaseInfo. Подойдёт любой объект, имеющий поле Name
        :param info_base_user: Пользователь ИБ с правами администратора
        :param info_base_pwd: Пароль пользователя ИБ
        :return: tuple(Наименование, Версия информационной базы)
        """
        external_connection = self.V8COMConnector.Connect(
            'Srvr="{0}";Ref="{1}";Usr="{2}";Pwd="{3}";'.format(self.host, info_base, info_base_user, info_base_pwd)
        )
        version = external_connection.Metadata.Version
        name = external_connection.Metadata.Name
        del external_connection
        return name, version

    def lock_info_base(self, working_process_connection, info_base, permission_code='0000',
                       message='Выполняется обслуживание ИБ'):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param working_process_connection: Соединение с рабочим процессом
        :param info_base: COM-Объект класса IInfoBaseInfo
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        # TODO: необходима проверка, есть ли у рабочего процесса необходимые авторизационные данные для этой ИБ
        info_base.ScheduledJobsDenied = True
        info_base.SessionsDenied = True
        info_base.PermissionCode = permission_code
        info_base.DeniedMessage = message
        working_process_connection.UpdateInfoBase(info_base)
        logging.debug('[{0}] Lock info base successfully'.format(info_base.Name))

    def unlock_info_base(self, working_process_connection, info_base):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param working_process_connection: Соединение с рабочим процессом
        :param info_base: COM-Объект класса IInfoBaseInfo
        """
        info_base.ScheduledJobsDenied = False
        info_base.SessionsDenied = False
        info_base.DeniedMessage = ""
        working_process_connection.UpdateInfoBase(info_base)
        logging.debug('[{0}] Unlock info base successfully'.format(info_base.Name))

    def terminate_info_base_sessions(self, agent_connection, cluster, info_base_short):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param agent_connection: Соединение с агентом сервера
        :param cluster: Класер серверов
        :param info_base_short: COM-Объект класса IInfoBaseShort
        """
        info_base_sessions = agent_connection.GetInfoBaseSessions(cluster, info_base_short)
        for session in info_base_sessions:
            agent_connection.TerminateSession(cluster, session)
