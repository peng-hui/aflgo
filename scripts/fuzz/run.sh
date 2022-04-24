#rm -rf temp *.bc
#rm -rf ./cpg.bin  obj-aflgo
export JOERN=/root/joern
export AFLGO=/root/aflgo
export SUBJECT=$PWD; export TMP_DIR=$PWD/obj-aflgo/temp
mkdir -p $TMP_DIR

$JOERN/joern-parse .
$JOERN/joern-export --repr cdg --out $TMP_DIR/cdg
$JOERN/joern-export --repr ast --out $TMP_DIR/ast

export CC=$AFLGO/afl-clang-fast; export CXX=$AFLGO/afl-clang-fast++
export LDFLAGS="-lpthread"
export ADDITIONAL="-targets=$TMP_DIR/BBtargets.txt -outdir=$TMP_DIR -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"
echo $'mjs.c:13732' > $TMP_DIR/BBtargets.txt
$CC -DMJS_MAIN mjs.c $ADDITIONAL -ldl -g -o mjs-bin
cat $TMP_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > $TMP_DIR/BBnames2.txt && mv $TMP_DIR/BBnames2.txt $TMP_DIR/BBnames.txt
cat $TMP_DIR/BBcalls.txt | sort | uniq > $TMP_DIR/BBcalls2.txt && mv $TMP_DIR/BBcalls2.txt $TMP_DIR/BBcalls.txt
$AFLGO/scripts/genDistance.sh $SUBJECT $TMP_DIR mjs-bin
$CC -DMJS_MAIN mjs.c -distance=$TMP_DIR/distance.cfg.txt -ldl -g -o mjs-bin
cd obj-aflgo; mkdir in; echo "" > in/in
$AFLGO/afl-fuzz -m none -z exp -c 45m -i in -o out ../mjs-bin -f @@
# mkdir out; for i in {1..10}; do timeout -sHUP 180m $AFLGO/afl-fuzz -m none -z exp -c 45m -i in -o "out/out_$i" ../mjs-bin -f @@ > /dev/null 2>&1 & done
