#Fuzzer

Firstly to install all requirements run:
 - pip freeze > requirements.txt

Run instructions part 0:
 - run Xampp DVWA
 - run: `python3 fuzz.py discover http://localhost/dvwa --custom-auth=dvwa`
 
 Run instructions par 1:
 - run Xampp DVWA
 - run: `python3 fuzz.py discover http://localhost/dvwa --custom-auth=dvwa --common-words=data/common_names.txt --extensions=data/base_extensions.txt`
 - you can optionally add in your own extensions.txt and or common.txt and pass in their file names
 - output will show, links guessed with files, links found recursively, cookies, and all page inputs
 
 
 Run instructions par 2:
 - run Xampp DVWA
 - run: `test http://localhost/dvwa/ --custom-auth=dvwa --common-words=data/common_names.txt --extensions=data/base_extensions.txt --common-words=data/common_names.txt --extensions=data/base_extensions.txt --vectors=data/vectors.txt --sensitive=data/sensitive.txt --slow=500`
 - you can optionally add in your own extensions.txt, common.txt, vectors.txt, or sensitive.txt and pass in their file names
 - output will show, links guessed with files, links found recursively, cookies, and all page inputs
 - output will also show any unsanitized inputs, potential DOS, and any links that return error codes