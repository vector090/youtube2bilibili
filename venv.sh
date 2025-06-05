
# source this file
VD=/tmp/v1
python -m venv $VD
source $VD/bin/activate

pip install -r requirements.txt

ffmpeg -version || apt install -y ffmpeg

