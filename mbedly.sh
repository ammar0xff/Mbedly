#!/bin/bash

# Colors
Black='\033[0;30m'
White='\033[1;37m'
green='\033[0;32m'
yellow='\033[1;33m'
Red='\033[0;31m'
Blue='\033[0;34m'
Purple='\033[0;35m'
Cyan='\033[0;36m'
Brown_Orange='\033[0;33m'
Dark_Gray='\033[1;30m'
Light_Green='\033[1;32m'
Light_Red='\033[1;31m'
Light_Cyan='\033[1;36m'
Light_Gray='\033[0;37m'
Light_Purple='\033[1;35m'
Light_Blue='\033[1;34m'
ENDCOLOR="\e[0m"


SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"



# The Functions
function general_link_extract {
    echo "analising the source for any urls"
    curl -s $1 \
        | grep 'http' \
        | tr " " "\n"  \
        | tr ">" "\n" \
        | tr '<' "\n" \
        | tr '`' "\n" \
        | tr '"' "\n" \
        | tr '(' "\n"\
        | tr "'" "\n" \
        | tr -d '[' \
        | tr -d ']' \
        | tr -d '\' 2> /dev/null \
        | grep -v "channel" \
        | grep -v "Quickbooks" \
        | sed 's/^.*http/http/' \
        | sort \
        | uniq\
        | grep "http" ;}


function yt_dl {
    case $1 in

        "144p")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=144][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=144]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "360p")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=360][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=360]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "480p")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=480][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=480]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "720p")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=720][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s"
            ;;

        "1080p")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=1080][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=1080]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "2k")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=1440][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=1440]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "4k")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestvideo[height=2160][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height=2160]+bestaudio --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s" 
            ;;

        "mp3")
            echo -e "${Green}downloaing $2 as format $1"
            $SCRIPT_DIR/loaders/yt-dlp $2 -f bestaudio -x --embed-thumbnail --audio-format mp3 --newline --quiet --progress --ignore-config --no-playlist --no-warnings  -o "%(title).200s"
            ;;
    esac
}


function yt_data_extractor {
        YT_title=$(curl -s   "https://www.youtube.com/oembed?url=http%3A//youtube.com/watch%3Fv%3D$1&format=json" | tr "{" "\n" | tr "}" "\n" | tr "," "\n" | tr -d '"' | grep "title"       | grep -v html  | cut -d ":" -f 2)
        YT_channel=$(curl -s "https://www.youtube.com/oembed?url=http%3A//youtube.com/watch%3Fv%3D$1&format=json" | tr "{" "\n" | tr "}" "\n" | tr "," "\n" | tr -d '"' | grep "author_name" | grep -v html  | cut -d ":" -f 2)
        echo -e "$Blue   Video name:$ENDCOLOR $YT_title "
        echo -e "$Blue   Channel:$ENDCOLOR $YT_channel " ;}


function yt_id_extractor {
    if [ $(echo $1 | grep -c "youtu.be") -eq 1 ]; then
        echo $1 | cut -d '/' -f 4 

    elif [ $(echo $1 | grep -c "watch") -eq 1 ]; then
        echo $1 | cut -d "?" -f 2 | tr -d "v="

    elif [ $(echo $1 | grep -c "embed") -eq 1 ]; then
        echo $1 | cut -d "/" -f 5

    elif [ $(echo $1 | grep -c "shorts") -eq 1 ]; then
        echo $1 | cut -d "/" -f 5
    fi;}


function maharatech_extractor {
    # echo -e "\n${Light_Green}[*] Detected Mahara Tech Course: ${ENDCOLOR}\n"  
    n=0
    url=$1
    cookie=$2
    function ExtractCourseVideoLinksFirst {
        curl -s --cookie $cookie "$url" \
            | grep 'http' \
            | tr " " "\n"  \
            | tr ">" "\n" \
            | tr '<' "\n" \
            | tr '`' "\n" \
            | tr '"' "\n" \
            | tr '(' "\n"\
            | tr "'" "\n" \
            | tr -d '[' \
            | tr -d ']' \
            | tr -d '\' 2> /dev/null \
            | grep -v "channel" \
            | grep -v "Quickbooks" \
            | sed 's/^.*http/http/' \
            | sort \
            | uniq\
            | grep "http" | grep hvp | grep -v "image"
    }
    CourseVDS=$(ExtractCourseVideoLinksFirst)
    while read video; do
        mahara_extract_process=$(curl -s --cookie $cookie "$video" \
            | grep 'http' \
            | tr " " "\n"  \
            | tr ">" "\n" \
            | tr '<' "\n" \
            | tr '`' "\n" \
            | tr '"' "\n" \
            | tr '(' "\n"\
            | tr "'" "\n" \
            | tr -d '[' \
            | tr -d ']' \
            | tr -d '\' 2> /dev/null \
            | grep -v "channel" \
            | grep -v "Quickbooks" \
            | sed 's/^.*http/http/' \
            | sort \
            | uniq\
            | grep "http" \
            | grep "youtu")


        while read -r ss; do
            echo -e "${Light_Green}[*] dumping course content #${n}.. "
            yt_data_extractor $(yt_id_extractor $ss)
            echo -e "$Blue   Video Link:$ENDCOLOR $ss \n" 

            n=$(($n+1))
        done <<< $mahara_extract_process
        mahara_extracted="$mahara_extracted
    $mahara_extract_process"
        done <<< $CourseVDS 
}





function a7a {

general_extracted=$(general_link_extract $URL)
filtered_URLS="$filtered_URLS
$general_extracted"

if [ $(echo $URL | grep -c "maharatech") -eq 1 ] && [ $(echo $URL | grep -c "course") -eq 1 ]  ; then
        title=$(curl -s "$URL" |  grep breadcrumb_title | grep h4 | cut -d '"' -f 3 | cut -d "<" -f 1 | tr -d ">")

        echo -e "\n${Light_Green}[*] Detected Mahara-Tech Course: ${ENDCOLOR}$title\n"  
        echo -n -e "\n${Light_Green}[!] Enter Your cookies in header string format (cookie editor export): ${ENDCOLOR}"  
        read maharaK

    maharatech_extractor $URL "${maharaK}"
        YT_LINK="$YT_LINK
$mahara_extracted"
elif [[ $URL =~ (youtu|youtu.be|watch|embed|shorts) ]]; then
        echo -e "\n${Light_Green}[*] Reading The YouTube Video Data..${ENDCOLOR}"  
        yt_data_extractor $(yt_id_extractor $URL)
        echo -e "$Blue   Video Link:$ENDCOLOR $URL \n" 
        YT_LINK="$YT_LINK
$URL"

else

    while read -r line; do
    if [ $(echo $line | grep -c "youtu") -eq 1 ]; then
        echo -e "\n${Light_Green}[*] Detected YouTube Video: ${ENDCOLOR}"  
        yt_data_extractor $(yt_id_extractor $line)
        echo -e "$Blue   Video Link:$ENDCOLOR $line \n" 
        YT_LINK="$YT_LINK
        $line"

    elif [ $(echo $line | grep -c "facebook.com/watch/?v=") -eq 1 ]; then
        echo -e "$green[*]$ENDCOLOR Detected Facebook Link:$Blue $line $ENDCOLOR" 
        YT_LINK="$YT_LINK
        $line"



    elif [ $(echo $line | grep -c ".liiivideo.com/embe") -eq 1 ]; then 
        echo -e "$green[*]$ENDCOLOR Detected LiiiVideo Link:$Blue $line $ENDCOLOR" 
        YT_LINK="$YT_LINK
        $line"


    elif [ $(echo $line | grep -c ".mp4") -eq 1 ]; then 
        echo -e "$green[*]$ENDCOLOR Detected Native Video:$Blue $line $ENDCOLOR"
        YT_LINK="$YT_LINK
        $line"


    fi 
    done <<< $filtered_URLS
fi
SAVEIFS=$IFS
IFS=$'\n'
YT_LINK=($YT_LINK)
IFS=$SAVEIFS

if [[ ${#YT_LINK[@]} = 1 ]]; then

echo -e "${Light_Green}[*] Your videos is ready to download, please select a quality.${ENDCOLOR}\n"

echo -e "${green}1. 144p
2. 360p
3. 480p
4. 720p
5. 1080p
6. 2k
7. 4k
8. mp3 (audio) $ENDCOLOR\n"

echo -e -n "${Light_Green}Select a Format (1-8): ${ENDCOLOR}"
read FORMAT


    YT_LINK="${YT_LINK[0]}"

case "$FORMAT" in
1)
    yt_dl "144p" "${YT_LINK[$b]}"
    ;;
2)
    yt_dl "360p" "${YT_LINK[$b]}"
    ;;
3)
    yt_dl "480p" "${YT_LINK[$b]}"
    ;;
4)
    yt_dl "720p" "${YT_LINK[$b]}"
    ;;
5)
    yt_dl "1080p" "${YT_LINK[$b]}"
    ;;
6)
    yt_dl "2k" "${YT_LINK[$b]}"
    ;;
7)
    yt_dl "4k" "${YT_LINK[$b]}"
    ;;
8)
    yt_dl "mp3" "${YT_LINK[$b]}"
    ;;
esac
exit
fi
echo -n -e "${Purple}Select Video Number or ALL: ${ENDCOLOR}"
read b

echo -e "${Light_Green}[*] Your videos is ready to download, please select a quality.${ENDCOLOR}\n"

echo -e "${green}1. 144p
2. 360p
3. 480p
4. 720p
5. 1080p
6. 2k
7. 4k
8. mp3 (audio) $ENDCOLOR\n"

echo -e -n "${Light_Green}Select a Format (1-8): ${ENDCOLOR}"
read FORMAT

if [[ "$b" == "ALL" ]]; then
    YT_Download=$(for (( i=0; i<${#YT_LINK[@]}; i++ )); do
        echo "${YT_LINK[$i]}"
    done)


    while read -r video; do
        case "$FORMAT" in
        1)
            yt_dl "144p" "$video"
            ;;
        2)
            yt_dl "360p" "$video"
            ;;
        3)
            yt_dl "480p" "$video"
            ;;
        4)
            yt_dl "720p" "$video"
            ;;
        5)
            yt_dl "1080p" "$video"
            ;;
        6)
            yt_dl "2k" "$video"
            ;;
        7)
            yt_dl "4k" "$video"
            ;;
        8)
            yt_dl "mp3" "$video"
            ;;
        esac
    done <<< "$YT_Download"

    exit
fi

YT_LINK="${YT_LINK[$b]}"

case "$FORMAT" in
1)
    yt_dl "144p" "${YT_LINK[$b]}"
    ;;
2)

    yt_dl "360p" "${YT_LINK[$b]}"

    ;;

3)
    yt_dl "480p" "${YT_LINK[$b]}"
    ;;
4)
    yt_dl "720p" "${YT_LINK[$b]}"
    ;;
5)
    yt_dl "1080p" "${YT_LINK[$b]}"
    ;;
6)
    yt_dl "2k" "${YT_LINK[$b]}"
    ;;
7)
    yt_dl "4k" "${YT_LINK[$b]}"
    ;;
8)
    yt_dl "mp3" "${YT_LINK[$b]}"
    ;;
esac


}





while test $# -gt 0; do
  case "$1" in
    -h|--help)
      echo "$0 [options] link"
      echo " "
      echo "Mbedly is 'Video Downloader/Web Scraber' Supports Many Sites And Makes A Video From Literally Everything!!"
      echo ""
      echo "options:"
      echo "-h, --help                show this help menu"
      echo "-l, --action=ACTION       link"
      exit 0
      ;;
    -l)
      URL=$2
      a7a
      exit
      ;;
  esac
done





# The Banner

echo -e "${yellow}                                                                   ${ENDCOLOR}"
echo -e "${yellow}   ██████   ██████ █████                  █████ ████               ${ENDCOLOR}"
echo -e "${yellow}   ░░██████ ██████ ░░███                  ░░███ ░░███              ${ENDCOLOR}"
echo -e "${yellow}   ░███░█████░███  ░███████   ██████   ███████  ░███  █████ ████   ${ENDCOLOR}"
echo -e "${yellow}   ░███░░███ ░███  ░███░░███ ███░░███ ███░░███  ░███ ░░███ ░███    ${ENDCOLOR}"
echo -e "${yellow}   ░███ ░░░  ░███  ░███ ░███░███████ ░███ ░███  ░███  ░███ ░███    ${ENDCOLOR}"
echo -e "${yellow}   ░███      ░███  ░███ ░███░███░░░  ░███ ░███  ░███  ░███ ░███    ${ENDCOLOR}"
echo -e "${yellow}   █████     █████ ████████ ░░██████ ░░████████ █████ ░░███████    ${ENDCOLOR}"
echo -e "${yellow}   ░░░░░     ░░░░░ ░░░░░░░░   ░░░░░░   ░░░░░░░░ ░░░░░   ░░░░░███   ${ENDCOLOR}"
echo -e "${yellow}                                                       ███ ░███    ${ENDCOLOR}"
echo -e "${yellow}        ${Brown_Orange}Made With <3 By ammar mohamed (ammar0xff)${ENDCOLOR}${yellow}     ░░██████    ${ENDCOLOR}"
echo -e "${yellow}                                                       ░░░░░░      ${ENDCOLOR}"
echo -e "${Light_Gray}Note: Only Youtube Suppourted for now •ᴗ•${ENDCOLOR} "
echo -n -e "${yellow}Enter a url contains a embeded video : ${ENDCOLOR}"
read -r URL




general_extracted=$(general_link_extract $URL)
filtered_URLS="$filtered_URLS
$general_extracted"

if [ $(echo $URL | grep -c "maharatech") -eq 1 ] && [ $(echo $URL | grep -c "course") -eq 1 ]  ; then
        title=$(curl -s "$URL" |  grep breadcrumb_title | grep h4 | cut -d '"' -f 3 | cut -d "<" -f 1 | tr -d ">")


        echo -e "\n${Light_Green}[*] Detected Mahara-Tech Course: ${ENDCOLOR}$title"  

        echo -n -e "\n${Light_Green}[!] Enter Your cookies in header string format (cookie editor export): ${ENDCOLOR}"  
        read maharaK

    maharatech_extractor $URL "${maharaK}"
        YT_LINK="$YT_LINK
$mahara_extracted"
elif [[ $URL =~ (youtu|youtu.be|watch|embed|shorts) ]]; then
        echo -e "\n${Light_Green}[*] Reading The YouTube Video Data..${ENDCOLOR}"  
        yt_data_extractor $(yt_id_extractor $URL)
        echo -e "$Blue   Video Link:$ENDCOLOR $URL \n" 
        YT_LINK="$YT_LINK
$URL"

else

    while read -r line; do
    if [ $(echo $line | grep -c "youtu") -eq 1 ]; then
        echo -e "\n${Light_Green}[*] Detected YouTube Video: ${ENDCOLOR}"  
        yt_data_extractor $(yt_id_extractor $line)
        echo -e "$Blue   Video Link:$ENDCOLOR $line \n" 
        YT_LINK="$YT_LINK
        $line"

    elif [ $(echo $line | grep -c "facebook.com/watch/?v=") -eq 1 ]; then
        echo -e "$green[*]$ENDCOLOR Detected Facebook Link:$Blue $line $ENDCOLOR" 
        YT_LINK="$YT_LINK
        $line"



    elif [ $(echo $line | grep -c ".liiivideo.com/embe") -eq 1 ]; then 
        echo -e "$green[*]$ENDCOLOR Detected LiiiVideo Link:$Blue $line $ENDCOLOR" 
        YT_LINK="$YT_LINK
        $line"


    elif [ $(echo $line | grep -c ".mp4") -eq 1 ]; then 
        echo -e "$green[*]$ENDCOLOR Detected Native Video:$Blue $line $ENDCOLOR"
        YT_LINK="$YT_LINK
        $line"


    fi 
    done <<< $filtered_URLS
fi
SAVEIFS=$IFS
IFS=$'\n'
YT_LINK=($YT_LINK)
IFS=$SAVEIFS

if [[ ${#YT_LINK[@]} = 1 ]]; then

echo -e "${Light_Green}[*] Your videos is ready to download, please select a quality.${ENDCOLOR}\n"

echo -e "${green}1. 144p
2. 360p
3. 480p
4. 720p
5. 1080p
6. 2k
7. 4k
8. mp3 (audio) $ENDCOLOR\n"

echo -e -n "${Light_Green}Select a Format (1-8): ${ENDCOLOR}"
read FORMAT


    YT_LINK="${YT_LINK[0]}"

case "$FORMAT" in
1)
    yt_dl "144p" "${YT_LINK[$b]}"
    ;;
2)
    yt_dl "360p" "${YT_LINK[$b]}"
    ;;
3)
    yt_dl "480p" "${YT_LINK[$b]}"
    ;;
4)
    yt_dl "720p" "${YT_LINK[$b]}"
    ;;
5)
    yt_dl "1080p" "${YT_LINK[$b]}"
    ;;
6)
    yt_dl "2k" "${YT_LINK[$b]}"
    ;;
7)
    yt_dl "4k" "${YT_LINK[$b]}"
    ;;
8)
    yt_dl "mp3" "${YT_LINK[$b]}"
    ;;
esac
exit
fi
echo -n -e "${Purple}Select Video Number or ALL: ${ENDCOLOR}"
read b

echo -e "${Light_Green}[*] Your videos is ready to download, please select a quality.${ENDCOLOR}\n"

echo -e "${green}1. 144p
2. 360p
3. 480p
4. 720p
5. 1080p
6. 2k
7. 4k
8. mp3 (audio) $ENDCOLOR\n"

echo -e -n "${Light_Green}Select a Format (1-8): ${ENDCOLOR}"
read FORMAT

if [[ "$b" == "ALL" ]]; then
    YT_Download=$(for (( i=0; i<${#YT_LINK[@]}; i++ )); do
        echo "${YT_LINK[$i]}"
    done)


    while read -r video; do
        case "$FORMAT" in
        1)
            yt_dl "144p" "$video"
            ;;
        2)
            yt_dl "360p" "$video"
            ;;
        3)
            yt_dl "480p" "$video"
            ;;
        4)
            yt_dl "720p" "$video"
            ;;
        5)
            yt_dl "1080p" "$video"
            ;;
        6)
            yt_dl "2k" "$video"
            ;;
        7)
            yt_dl "4k" "$video"
            ;;
        8)
            yt_dl "mp3" "$video"
            ;;
        esac
    done <<< "$YT_Download"

    exit
fi

YT_LINK="${YT_LINK[$b]}"

case "$FORMAT" in
1)
    yt_dl "144p" "${YT_LINK[$b]}"
    ;;
2)

    yt_dl "360p" "${YT_LINK[$b]}"

    ;;

3)
    yt_dl "480p" "${YT_LINK[$b]}"
    ;;
4)
    yt_dl "720p" "${YT_LINK[$b]}"
    ;;
5)
    yt_dl "1080p" "${YT_LINK[$b]}"
    ;;
6)
    yt_dl "2k" "${YT_LINK[$b]}"
    ;;
7)
    yt_dl "4k" "${YT_LINK[$b]}"
    ;;
8)
    yt_dl "mp3" "${YT_LINK[$b]}"
    ;;
esac











