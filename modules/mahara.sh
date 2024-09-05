#!/bin/bash

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
    curl -s --cookie $cookie "$video" \
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
        | grep "youtu"
        
    done <<< $CourseVDS
