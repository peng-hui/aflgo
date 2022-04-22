rm -rf temp *.bc
rm -rf ./cpg.bin 
 mkdir temp
#$LIBS=`llvm-config --libs $(LLVM_MODULES)`
export JOERN=/root/joern
export AFLGO=/root/aflgo
export SUBJECT=$PWD; export TMP_DIR=$PWD/temp
export CC=$AFLGO/afl-clang-fast; export CXX=$AFLGO/afl-clang-fast++
export LDFLAGS="-lpthread"
export ADDITIONAL="-targets=$TMP_DIR/BBtargets.txt -outdir=$TMP_DIR -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"
echo "$1:2" > $TMP_DIR/BBtargets.txt
$CC $1 -lLLVMDemangle $LDFALGS $ADDITIONAL -o a.out
cat $TMP_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > $TMP_DIR/BBnames2.txt && mv $TMP_DIR/BBnames2.txt $TMP_DIR/BBnames.txt
cat $TMP_DIR/BBcalls.txt | sort | uniq > $TMP_DIR/BBcalls2.txt && mv $TMP_DIR/BBcalls2.txt $TMP_DIR/BBcalls.txt
$AFLGO/scripts/genDistance.sh $SUBJECT $TMP_DIR a.out
$JOERN/joern-parse $1
$JOERN/joern-export --repr cdg --out $TMP_DIR/cdg
$JOERN/joern-export --repr ast --out $TMP_DIR/ast
$AFLGO/scripts/callgraph.py -t $TMP_DIR/BBtargets.txt -c $TMP_DIR/cdg -a $TMP_DIR/ast -cg $TMP_DIR/distance.callgraph.txt -bc $TMP_DIR/BBcalls.txt -fl $TMP_DIR/funcloc.txt


#$CC -DMJS_MAIN $1 -distance=$TMP_DIR/distance.cfg.txt -ldl -g -o a1.out
#!bash
#cd obj-aflgo; mkdir in; echo "" > in/in
#$AFLGO/afl-fuzz -m none -z exp -c 45m -i in -o out ../mjs-bin -f @@
# mkdir out; for i in {1..10}; do timeout -sHUP 180m $AFLGO/afl-fuzz -m none -z exp -c 45m -i in -o "out/out_$i" ../mjs-bin -f @@ > /dev/null 2>&1 & done

