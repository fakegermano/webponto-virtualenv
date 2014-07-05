from django.db import models
from django.conf import settings
from datetime import datetime, date, time
# Create your models here.

# Model para gerenciar os plantoes dos membros
# cadastrando no bd:
# - Quem criou o plantao
# - Quando o plantao foi criado (automatico)
# - O titulo do plantao
# - A ultima data que o plantao ocorrera (opcional)
# - o Membro que realizara o plantao
class Plantao(models.Model):
    # TODO: Coletar automaticamente o usuario que esta
    # logado no sistema.
    # TODO: sistema de permissoes, usuario qualquer nao consegue
    # isso fica facil com a api de usuario do django
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=u'Criado por',
    )
    # data de criacao do plantao... automatico!
    # simplesmente para controle.
    criado_em = models.DateTimeField(
        verbose_name=u'Data de criacao',
        auto_now_add=True, editable=False,
    )
    # Titulo do plantao, para facilitar a leitura pelo admin
    # TODO: Utilidade disso!?!
    titulo = models.CharField(
        max_length=256,
        verbose_name=u'Titulo',
    )
    # Field opicional, eh a ultima data que o plantao ocorrera
    # para facilitar o controle de fazer plantoes que sao em apenas
    # um semestre
    ultima_data = models.DateTimeField(
        verbose_name=u'Ultima data',
        blank=True, null=True,
    )
    # O membro que fara o plantao
    # TODO: fazer isso ser listado no painel do membro
    membro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=u'Nome do membro',
        related_name='+',
    )
    # meta para manipular os filtros.
    # e os nomes em portugues (django derpa em Port)
    class Meta:
        get_latest_by = ['criado_por']
        ordering = ['ultima_data', 'criado_por']
        verbose_name=u'Plantao'
        verbose_name_plural=u'Plantoes'

    # Define como o Modelo sera vizualizado no painel
    # de administrador
    # TODO: fazer algo melhor que isso, fica muito confuso!!!
    # alem de titulo ser inutir?!?
    def __unicode__(self):
        return u'%s %s' % (self.titulo, self.membro)

    # metodo que lista todas as ocorrencias relacionadas a este
    # plantao! Para facilitar a edicao e visualizacao.
    # TODO: melhorar a forma como isso esta relacionado
    # no momento da insercao de um novo plantao
    # isso fica facil com a API 'inline' do django.admin
    def lista_ocorrencias(self):
        return Ocorrencia.objects.filter(plantao=self)

# Model para gerenciar as ocorrencias dos plantoes
# guarda os seguintes dados no bd:
# - inicio: data de inicio da ocorrencia
# - final: data final da ocorrencia (automatico, com base na duracao)
# - duracao: duracao em horas do plantao
# - plantao: plantao que essa ocorrencia esta relacionada no bd
# - cancelado: field para facilitar o cancelamento de um plantao
# - presenca: field para ver quando o membro esteve presente, ausente ou
# justificou a presenca no plantao
class Ocorrencia(models.Model):
    # data de inicio da ocorrencia
    # TODO: a data da ocorrencia eh sempre a mesma
    # o horario de inicio e de final eh que mudam
    # tentar implementar isso!
    # (vai facilitar na hora de visualizar o calendario)
    inicio = models.DateTimeField(
        verbose_name=u'Data de inicio',
    )
    # duracao da ocorrencia do plantao em horas
    # TODO: deixar opcoes: escolher entre 1h e 2h (coordenador e assessor)
    # TODO2: viabilidade disso! Talvez deixar assim pra facilitar a insercao
    # de eventos que nao sao plantoes no caledario.
    duracao = models.IntegerField(
        verbose_name=u'Duracao da ocorrencia',
    )
    # mesmo TODO do plantao: auto-add com base no login!
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=u'Criado por',
    )
    # plantao que essa ocorrencia se relaciona
    plantao = models.ForeignKey(
        'Plantao',
        verbose_name=u'Plantao',
    )
    # se o plantao foi cancelado ou nao
    # TODO: fazer isso ser utilizado na listagem de ocorrencias
    cancelado = models.BooleanField(
        verbose_name=u'Cancelado',
        default=False,
    )
    # auxiliar:
    # TODO: tirar isso daqui e colocar em um arquivo
    # constantes.py ou algo assim.. soh polui o codigo
    PRESENCAS= {
        'PORVIR':u'PORVIR',
        'PRESENTE':u'PRESENTE',
        'AUSENTE':u'AUSENTE',
        'JUSTIFICADO':u'JUSTIFICADO',
    }
    # auxiliar tbm
    PRESENCAS_ESCOLHAS=(
        (PRESENCAS['PRESENTE'], u'Presente'),
        (PRESENCAS['AUSENTE'], u'Ausente'),
        (PRESENCAS['JUSTIFICADO'], u'Justificado'),
        (PRESENCAS['PORVIR'], u'Plantao por vir'),
    )
    # seta se o membro esteve presente ou nao
    # TODO: deixar mais bonito esse esquema de plantao por vir,
    # ou seja, fazer essa selecao do valor no BD funcionar so quando
    # chegar(ou passar) a data do plantao
    # MUITO LATE GAME ISSO AQUI
    presenca = models.CharField(
        choices=PRESENCAS_ESCOLHAS,
        max_length=15,
        null=True,blank=True,
    )

    # como a ocorrencia eh visualisada pelo painel de admin
    # TODO: deixar isso mais util em questao de visualizacao mesmo
    def __unicode__(self):
        return u'Ocorrencia em %s' % (self.inicio.strftime('%d, %b'))

    # metodo auxiliar para determinar a data final do plantao
    def _set_final(self):
        hora = self.inicio.hour + self.duracao
        data = datetime.combine(self.inicio.date(),
                                time(hora, self.inicio.minute))
        return data
    # isso aqui eh dahora =P o atributo eh temporario e eh definido
    # por uma funcao.. depois eu adiciono ele no BD sobrescrevendo
    # o metodo save do model!
    final_prop = property(_set_final)

    # data final do plantao:
    # mesmo TODO da inicial!
    final = models.DateTimeField(
        verbose_name=u'Data de Termino',
        editable=False,
    )
    # sobrescrevo o metodo save para colocar
    # o valor da data final no bd..
    def save(self, *args, **kwargs):
        # auto-add a data final com base da duracao
        self.final = self.final_prop
        # seta automaticamente a ultima_data do plantao associado
        # caso isso ja nao tenha sido feito.
        if self.plantao.ultima_data == None or self.inicio > self.plantao.ultima_data:
            self.plantao.ultima_data = self.inicio
            self.plantao.save()
        super(Ocorrencia, self).save(*args, **kwargs)
