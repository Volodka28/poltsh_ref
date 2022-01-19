#!/bin/bash
umask 0007


echo $(date '+%d.%m.%Y %H:%M:%S.%3N') >> time_file.txt


PROGNAME="{start_str}"

HOURS_COUNT=120 # ������� ����� �������
#MINUTS_TO_STOP=50 # �� ������� ����� �� ����� ������ ���������������; 0 - �� �������������

NODES_COUNT={nodes_count}
SLURMCPUNODE="`echo $SLURM_JOB_CPUS_PER_NODE | sed 's/(x[0-9]\+)$//'`"
JCPUNODE={jcpu_node} #$SLURMCPUNODE

OUTFILE=`mktemp -u .out.XXXXXXX`

rm -f $OUTFILE

if [ ! -n "$1" ]
then

	while [ 1 ]; do
	    sbatch -p {type_node} -t $(($HOURS_COUNT*60)) -N $NODES_COUNT $0 run 2>&1 | tee $OUTFILE
	    grep -q "Batch job submission failed" $OUTFILE || break
	    rm -f $OUTFILE
            exit 0
	done
	rm -f $OUTFILE
	exit 0
fi

[ -z "$SLURM_JOB_NODELIST" ] && exit 1



NODELIST=""
RES=`expr index $SLURM_JOB_NODELIST "[,"`
if [ $RES -ne 0 ]; then
    for e in `echo $SLURM_JOB_NODELIST | sed 's/,\([^0-9]\)/ \1/g'`; do
	RES=`expr index $e "["`
	if [ $RES -ne 0 ]; then
	    NBASE="`echo $e | sed 's/^\(.*\)\[.*$/\1/'`"
	    NLIST="`echo $e | sed 's/^.*\[\(.\+\)\]$/\1/;s/,/ /g'`"
	    for i in $NLIST; do
		RES=`expr index $i "-"`
		if [ $RES -ne 0 ]; then
		    x="`echo $i | cut -d- -f1`"
		    y="`echo $i | cut -d- -f2`"
		    for n in `seq -w $x $y`; do
			[ -z "$NODELIST" ] || NODELIST=$NODELIST","
			NODELIST=$NODELIST$NBASE$n:$JCPUNODE
		    done
		else
		    [ -z "$NODELIST" ] || NODELIST=$NODELIST","
		    NODELIST=$NODELIST$NBASE$i:$JCPUNODE
		fi
	    done
	else
	    [ -z "$NODELIST" ] || NODELIST=$NODELIST","
	    NODELIST=$NODELIST$e:$JCPUNODE
	fi
    done
else
	NODELIST=$SLURM_JOB_NODELIST:$JCPUNODE
fi





MASTER_HOST=`echo $NODELIST | cut -d: -f1`
THIS_HOST=`hostname -s`
LOCK_FILE=".lock.$SLURM_JOBID"

if [ ! "$THIS_HOST" = "$MASTER_HOST" ]; then
    sleep 30
    while [ -e $LOCK_FILE ]; do
	sleep 15
    done
    echo ">>> Slave host $THIS_HOST: Exiting..."#
#    exit 0
fi

touch $LOCK_FILE
touch job.$SLURM_JOBID



sleep 5


MYHOSTFILE="hostfile.$SLURM_JOBID"
rm -f $MYHOSTFILE
touch $MYHOSTFILE

MYHOSTFILE2="hostfile2.$SLURM_JOBID"
rm -f $MYHOSTFILE2
touch $MYHOSTFILE2

NODELIST=""
RES=`expr index $SLURM_JOB_NODELIST "[,"`
if [ $RES -ne 0 ]; then
    for e in `echo $SLURM_JOB_NODELIST | sed 's/,\([^0-9]\)/ \1/g'`; do
	RES=`expr index $e "["`
	if [ $RES -ne 0 ]; then
	    NBASE="`echo $e | sed 's/^\(.*\)\[.*$/\1/'`"
	    NLIST="`echo $e | sed 's/^.*\[\(.\+\)\]$/\1/;s/,/ /g'`"
	    for i in $NLIST; do
		RES=`expr index $i "-"`
		if [ $RES -ne 0 ]; then
		    x="`echo $i | cut -d- -f1`"
		    y="`echo $i | cut -d- -f2`"
		    for n in `seq -w $x $y`; do
			[ -z "$NODELIST" ] || NODELIST=$NODELIST","
			NODELIST=$NBASE$n:$JCPUNODE
echo $NODELIST >> $MYHOSTFILE
for i in $(seq 1 1 $JCPUNODE)
do
   echo $NBASE$n >> $MYHOSTFILE2
done
		    done
		else
		    [ -z "$NODELIST" ] || NODELIST=$NODELIST","
		    NODELIST=$NBASE$i:$JCPUNODE
echo $NODELIST >> $MYHOSTFILE
for ii in $(seq 1 1 $JCPUNODE)
do
   echo $NBASE$i >> $MYHOSTFILE2
done
		fi
	    done
	else
	    [ -z "$NODELIST" ] || NODELIST=$NODELIST","
	    NODELIST=$e:$JCPUNODE
echo $NODELIST >> $MYHOSTFILE
for i in $(seq 1 1 $JCPUNODE)
do
   echo $e >> $MYHOSTFILE2
done
	fi
    done
else
	NODELIST=$SLURM_JOB_NODELIST:$JCPUNODE
echo $NODELIST >> $MYHOSTFILE
for i in $(seq 1 1 $JCPUNODE)
do
   echo $SLURM_JOB_NODELIST >> $MYHOSTFILE2
done
fi

echo ">>> Master host $THIS_HOST: Starting computations..."
echo ">>> NODELIST = $NODELIST"

NCPU=`cat $MYHOSTFILE2 | wc -l`

unset INTEL_LICENSE_FILE
export LM_LICENSE_FILE=1055@login

echo "NCPU=$NCPU"



echo "ping:"
ping  login -c 4

if [ -f /lustre/software/lazurit/bashrc ]; then
	. /lustre/software/lazurit/bashrc
fi

export I_MPI_FABRICS=shm:ofi

sed -e 's/node0/node/g' ./$MYHOSTFILE2 > tmphostfile.txt
sed -e 's/node0/node/g' ./tmphostfile.txt > $MYHOSTFILE2

echo "export:"
export

echo "free:"
free

echo "cpuinfo:"
cat /proc/cpuinfo

echo "meminfo:"
cat /proc/meminfo

echo "ulimit -a:"
ulimit -a

echo ===============================================================================
#if [ "$MINUTS_TO_STOP" -ne "0" ]; then
#    sleep $(($HOURS_COUNT*60*60-$MINUTS_TO_STOP*60)) && echo "save" > $model.MOD && echo "STOP COMMAND SENDED" &
#fi
echo ===============================================================================
export PBS_NODEFILE=$MYHOSTFILE
export PBS_O_WORKDIR=`pwd`
PROGNAME = $LAZURITPATH/$PROGNAME
CMD="mpiexec.hydra -n $NCPU -machinefile $MYHOSTFILE2 $PROGNAME  > log.txt 2>>log_job.txt"

which mpiexec.hydra

echo "" >> log_job.txt
echo "============================================" >> log_job.txt
echo $HOSTNAME >> log_job.txt
echo "start" >> log_job.txt
echo "job CMD=$CMD" >> log_job.txt
echo "start :" `date` >> log_job.txt
eval $CMD
#mpiexec.hydra -n $NCPU -machinefile $MYHOSTFILE2 ./$PROGNAME  > log.txt 2>>log_job.txt
echo "stop  :" `date` >> log_job.txt

echo $(date '+%d.%m.%Y %H:%M:%S.%3N') >> time_file.txt
echo ===============================================================================

sync



rm -f $LOCK_FILE

echo ">>> Master host $THIS_HOST: Exiting..."


#epilog

### log_file -- лог теста
### calc_path --- путь расчёта задачи
### last_str --- последняя строка лога лазурита
### done_path --- путь до готовой задачи, успешно посчитанной


log_file={log_file}


calc_path=$(pwd)
etalon=" ======= Program Lazurit finish! ======="
cd "{utils_path}"
assignment_string=$(python check_status.py $calc_path)

eval $assignment_string


echo $last_str
echo $calc_path

# Выяснение правильности завершения расчёта и перемещение в папку done
cd $calc_path
if [ "$last_str" == "$etalon" ]
then
  echo "Задача $calc_path успешно завершена" >> $log_file
  mkdir -p $done_path
  for i in *; do mv "$calc_path/$i" "$done_path/$i"; echo $i;done

else
  echo "Задача $calc_path не успешно завершена" >> $log_file
fi

# Запуск утилиты для поспроцессинга 
## Выяснение вопроса: "Завершился ли весь кейс удачно?"
### Да --- Запуск отчета задачи и кейса; Нет --- запуск отчёта задачи

#Создание сводной таблицы по завершенным задачам


