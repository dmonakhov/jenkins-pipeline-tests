#!groovie


node {
     stage 'checkout test src'
     checkout scm
     
     stage 'Fetch kernel'
     try {
     	  sh 'rm -rf artifacts avocado/job-results'
          sh 'avjen avocado/linuxbuild2.py -m avocado/linuxbuild.py.data/v4.7.yaml'
     	  stash includes: 'artifacts/*', name: 'build-ctx'

          stage 'Build kernel'
	  sh 'find * -ls'
	  // unstash 'build-ctx'
          sh 'avjen avocado/linuxbuild3.py -m avocado/linuxbuild.py.data/v4.7.yaml'
	  stash includes: 'artifacts/bzImage', name: 'bzImage'
     } catch (error) {
          echo "Failed, error: ${error}"
	  sh 'find * -ls'
          step([$class: 'JUnitResultArchiver', testResults: '**/results.xml'])
          step([$class: 'ArtifactArchiver', artifacts: 'avocado/job-results/*/job.log', fingerprint: true])
          throw error
     }
}

stage 'Run test in parallel'

//def test_list = ["generic/001", "generic/002", "generic/013", "ext4/300", "ext4/301", "ext4/302" ]
def test_list = ["4k", "1k",  "ext3", "nojournal", "ext3conv", "metacsum", "dioread_nolock"]
//def test_list = ["generic/001"]
def stepsForParallel = [:]

for (int i = 0; i < test_list.size(); i++) {
    // Get the actual string here.
    def t = test_list.get(i)
    def stepName = "echoing ${t}"
    
    stepsForParallel[stepName] = transformIntoStep(t)
}

parallel stepsForParallel

def transformIntoStep(test) {
    return {
        node {
            echo test
	    checkout scm
	    unstash 'bzImage'

	    sh ' cp artifacts/bzImage /devel/docker/vols/src-mirror/'
	    withEnv(["CFG_NAME=${test}"]) {
	      echo "Run test: ${test}"
	      sh 'echo "CFG_NAME: ${CFG_NAME}" > test.yaml'
	      sh 'dav-jen avocado/xfstests-bld.sh -m test.yaml || /bin/true'
	    }
            step([$class: 'JUnitResultArchiver', testResults: '**/results.xml'])
	    step([$class: 'ArtifactArchiver', artifacts: 'avocado/job-results/*.tar.xz', fingerprint: true])
        }
    }
}
