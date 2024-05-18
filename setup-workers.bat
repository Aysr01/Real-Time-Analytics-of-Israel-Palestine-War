docker exec -it spark-worker1 pip install requests
docker exec -it spark-worker2 pip install requests
docker exec -it spark-master /bin/bash utils/start-job.sh